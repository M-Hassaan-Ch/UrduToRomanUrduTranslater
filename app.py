import streamlit as st
import torch
import torch.nn as nn
import sentencepiece as spm

# Model architecture classes
class Encoder(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_layers=1, pad_idx=0, dropout=0.1):
        super().__init__()
        self.embedding = nn.Embedding(num_embeddings=vocab_size, embedding_dim=embed_dim, padding_idx=pad_idx)
        self.lstm = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            bidirectional=True,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )

    def forward(self, src):
        embedded = self.embedding(src)
        outputs, (hidden, cell) = self.lstm(embedded)
        return outputs, (hidden, cell)

class DecoderLSTM(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_layers=1, pad_idx=0, dropout=0.1, encoder_bidirectional=False):
        super().__init__()
        self.vocab_size = vocab_size
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.encoder_bidirectional = encoder_bidirectional

        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)
        self.lstm = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.fc_out = nn.Linear(hidden_dim, vocab_size)

        if self.encoder_bidirectional:
            self.reduce_hidden = nn.Linear(hidden_dim * 2, hidden_dim)
            self.reduce_cell = nn.Linear(hidden_dim * 2, hidden_dim)

    def init_hidden_from_encoder(self, enc_hidden, enc_cell):
        num_enc_layers_times_dirs, batch, hidden_enc = enc_hidden.size()
        num_dirs = 2 if self.encoder_bidirectional else 1
        num_enc_layers = num_enc_layers_times_dirs // num_dirs

        enc_hidden = enc_hidden.view(num_enc_layers, num_dirs, batch, hidden_enc)
        enc_cell = enc_cell.view(num_enc_layers, num_dirs, batch, hidden_enc)

        if self.encoder_bidirectional:
            hidden_cat = torch.cat([enc_hidden[:, 0], enc_hidden[:, 1]], dim=2)
            cell_cat = torch.cat([enc_cell[:, 0], enc_cell[:, 1]], dim=2)
        else:
            hidden_cat = enc_hidden.squeeze(1)
            cell_cat = enc_cell.squeeze(1)

        hidden_proj = torch.tanh(self.reduce_hidden(hidden_cat))
        cell_proj = torch.tanh(self.reduce_cell(cell_cat))

        if self.num_layers > num_enc_layers:
            pad_layers = self.num_layers - num_enc_layers
            pad_hidden = torch.zeros(pad_layers, batch, self.hidden_dim, device=hidden_proj.device)
            pad_cell = torch.zeros(pad_layers, batch, self.hidden_dim, device=cell_proj.device)
            hidden_proj = torch.cat([hidden_proj, pad_hidden], dim=0)
            cell_proj = torch.cat([cell_proj, pad_cell], dim=0)
        elif self.num_layers < num_enc_layers:
            hidden_proj = hidden_proj[-self.num_layers:]
            cell_proj = cell_proj[-self.num_layers:]

        return hidden_proj, cell_proj

    def generate(self, hidden, cell, sos_id, eos_id, max_len=50):
        batch_size = hidden.size(1)
        device = hidden.device
        input_tok = torch.full((batch_size,), sos_id, dtype=torch.long, device=device)
        generated = []

        for _ in range(max_len):
            if input_tok.dim() == 1:
                input_tok = input_tok.unsqueeze(1)
            embedded = self.embedding(input_tok)
            output, (hidden, cell) = self.lstm(embedded, (hidden, cell))
            logits = self.fc_out(output.squeeze(1))
            next_tok = logits.argmax(1)
            generated.append(next_tok.unsqueeze(1))
            input_tok = next_tok
            if (next_tok == eos_id).all():
                break

        if len(generated) == 0:
            return torch.empty((batch_size, 0), dtype=torch.long, device=device)
        return torch.cat(generated, dim=1)

class Seq2Seq(nn.Module):
    def __init__(self, encoder, decoder, device):
        super().__init__()
        self.encoder = encoder
        self.decoder = decoder
        self.device = device

    def translate(self, src, sos_id, eos_id, max_len=50):
        enc_outputs, (enc_hidden, enc_cell) = self.encoder(src)
        dec_hidden, dec_cell = self.decoder.init_hidden_from_encoder(enc_hidden, enc_cell)
        generated = self.decoder.generate(dec_hidden, dec_cell, sos_id, eos_id, max_len=max_len)
        return generated

def load_models():
    try:
        # Load tokenizers
        st.info("Loading tokenizers...")
        urdu_tokenizer = spm.SentencePieceProcessor()
        urdu_tokenizer.load("urdu_tokenizer.model")
        roman_tokenizer = spm.SentencePieceProcessor()
        roman_tokenizer.load("roman_tokenizer.model")
        st.success("Tokenizers loaded successfully!")

        # Model parameters (same as training)
        INPUT_DIM = urdu_tokenizer.get_piece_size()
        OUTPUT_DIM = roman_tokenizer.get_piece_size()
        ENC_EMB_DIM = 256
        DEC_EMB_DIM = 256
        HIDDEN_DIM = 512
        ENC_LAYERS = 2
        DEC_LAYERS = 4
        ENC_DROPOUT = 0.3
        DEC_DROPOUT = 0.3
        
        # Create model architecture
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        encoder = Encoder(
            vocab_size=INPUT_DIM,
            embed_dim=ENC_EMB_DIM,
            hidden_dim=HIDDEN_DIM,
            num_layers=ENC_LAYERS,
            dropout=ENC_DROPOUT
        )
        
        decoder = DecoderLSTM(
            vocab_size=OUTPUT_DIM,
            embed_dim=DEC_EMB_DIM,
            hidden_dim=HIDDEN_DIM,
            num_layers=DEC_LAYERS,
            dropout=DEC_DROPOUT,
            encoder_bidirectional=True
        )
        
        model = Seq2Seq(encoder, decoder, device).to(device)
        
        # Load trained weights
        st.info("Loading model weights...")
        model.load_state_dict(torch.load("seq2seq_best.pt", map_location=device))
        model.eval()
        st.success("Model loaded successfully!")
        
        return urdu_tokenizer, roman_tokenizer, model

    except Exception as e:
        st.error(f"Error in load_models: {str(e)}")
        st.error(f"Error type: {type(e).__name__}")
        raise

def translate_text(text, urdu_tokenizer, roman_tokenizer, model):
    device = next(model.parameters()).device
    
    # Encode and prepare input
    input_tokens = urdu_tokenizer.encode(text, out_type=int)
    input_tokens = [urdu_tokenizer.bos_id()] + input_tokens + [urdu_tokenizer.eos_id()]
    input_tensor = torch.tensor([input_tokens], device=device)
    
    # Generate translation
    with torch.no_grad():
        sos_id = roman_tokenizer.bos_id()
        eos_id = roman_tokenizer.eos_id()
        outputs = model.translate(input_tensor, sos_id, eos_id, max_len=128)
    
    # Decode output
    output_tokens = outputs[0].cpu().tolist()
    filtered_tokens = [t for t in output_tokens if t not in [roman_tokenizer.pad_id(), roman_tokenizer.bos_id(), roman_tokenizer.eos_id()]]
    translated_text = roman_tokenizer.decode(filtered_tokens)
    return translated_text

# Set up the Streamlit page
st.set_page_config(page_title="Urdu to Roman Urdu Translator", layout="wide")

# Add a title
st.title("Urdu to Roman Urdu Translator")

# Add description
st.write("Enter Urdu text below to translate it to Roman Urdu.")

try:
    # Load models
    urdu_tokenizer, roman_tokenizer, model = load_models()
    
    # Create input text area
    input_text = st.text_area("Enter Urdu Text:", height=150)
    
    # Add translate button
    if st.button("Translate"):
        if input_text:
            with st.spinner("Translating..."):
                translated_text = translate_text(input_text, urdu_tokenizer, roman_tokenizer, model)
                st.subheader("Translation:")
                st.write(translated_text)
        else:
            st.warning("Please enter some text to translate.")

except Exception as e:
    st.error(f"Error: {str(e)}")
    st.info("Please make sure all required model files are in the correct location.")