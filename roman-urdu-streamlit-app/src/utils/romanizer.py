def romanize(urdu_text):
    # A simple mapping of Urdu characters to Roman Urdu equivalents
    urdu_to_roman = {
        'ا': 'a', 'ب': 'b', 'پ': 'p', 'ت': 't', 'ٹ': 'ṭ', 'ث': 's', 'ج': 'j', 
        'چ': 'ch', 'ح': 'h', 'خ': 'kh', 'د': 'd', 'ڈ': 'ḍ', 'ذ': 'z', 'ر': 'r', 
        'ز': 'z', 'ژ': 'zh', 'س': 's', 'ش': 'sh', 'ص': 'ṣ', 'ض': 'ẓ', 'ط': 'ṭ', 
        'ظ': 'ẓ', 'ع': '‘', 'غ': 'gh', 'ف': 'f', 'ق': 'q', 'ک': 'k', 'گ': 'g', 
        'ل': 'l', 'م': 'm', 'ن': 'n', 'ں': 'n', 'و': 'w', 'ہ': 'h', 'ء': ''
    }
    
    roman_text = ''
    for char in urdu_text:
        roman_text += urdu_to_roman.get(char, char)  # Default to the character itself if not found
    
    return roman_text.strip()  # Remove any leading/trailing whitespace