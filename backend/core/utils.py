import re

def normalize_title(title: str) -> str:
    """
    Hyper-aggressive normalization to catch fuzzy duplicates.
    Used for both cleaning and pre-upload checking.
    """
    # 1. Lowercase
    s = title.lower()
    
    # 2. Strip Vietnamese accents (comprehensive)
    accents = {
        'a': 'áàảãạăắằẳẵặâấầẩẫậ', 'e': 'éèẻẽẹêếềểễệ', 'i': 'íìỉĩị',
        'o': 'óòỏõọôốồổỗộơớờởỡợ', 'u': 'úùủũụưứừửữự', 'y': 'ýỳỷỹỵ', 'd': 'đ'
    }
    for char, group in accents.items():
        for accented in group:
            s = s.replace(accented, char)
    
    # 3. Remove common file junk and site tags
    s = re.sub(r'[-_\s]+xnhau', '', s)
    s = re.sub(r'\b(clip|video|full|st|phim|sex|hay)\b', '', s)
    
    # 4. Remove extension
    s = re.sub(r'\.[a-z0-9]{2,4}$', '', s)
    
    # 5. Remove all non-alphanumeric
    s = re.sub(r'[^a-z0-9]', '', s)
    
    # 6. Remove trailing numbers (versioning)
    if len(s) > 10:
        s = re.sub(r'\d+$', '', s)
        
    return s
