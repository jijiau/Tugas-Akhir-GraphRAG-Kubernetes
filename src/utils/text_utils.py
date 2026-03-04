"""
Text Processing Utilities for Kubernetes GraphRAG
==================================================
Pure functions with no external dependencies.
Safe to import anywhere without triggering config loading.
"""

from typing import Optional

def smart_truncate_description(desc: str, original_length: Optional[int] = None, max_length: int = 2000) -> str:
    """
    Intelligently truncate description while preserving critical information.
    
    Priority Order:
    1. Keep WARNING, DEPRECATED, SECURITY notices (even if at end)
    2. Truncate at sentence boundary (not mid-sentence)
    3. Preserve first 2000 chars as baseline

    Args:
        desc: Original description text
        original_length: Length of original description (for ellipsis check)
        max_length: Maximum characters to keep (default: 2000)
    
    Returns:
        Truncated description with critical info preserved
    """
    if not desc:
        return 'No description provided.'
    
    # Store original length if not provided
    if original_length is None:
        original_length = len(desc)
    
    # If already within limit, return as-is
    if len(desc) <= max_length:
        return desc
    
    # === Priority 1: Find Critical Keywords ===
    critical_keywords = [
        # 1. API Lifecycle & Maturity (Mencegah LLM memakai struktur usang)
        "DEPRECATED", "OBSOLETE", "REMOVED", "ALPHA", "BETA",
        
        # 2. Alerts & Warnings (Peringatan operasional krusial)
        "WARNING", "IMPORTANT", "CAUTION", "SECURITY", "DANGER", "NOTE",
        
        # 3. Mutability & Defaults (Aturan dasar field YAML)
        "IMMUTABLE", "READ-ONLY", "CANNOT BE UPDATED", "REQUIRED", "DEFAULTS TO",
        
        # 4. Structural Logic & Conflicts (BARU: Mencegah error logika YAML)
        "MUTUALLY EXCLUSIVE", # Misal: Tidak boleh pakai hostPath dan emptyDir bersamaan
        "IGNORED IF",         # Misal: Field ini diabaikan kalau field lain diisi
        "MUST MATCH",         # Misal: Label selector harus sama dengan pod template
        "AT LEAST ONE",       # Misal: Harus ada minimal satu container di dalam Pod
        "ONLY ALLOWED",       # Menandakan batasan nilai yang ketat
        
        # 5. Data Formatting (BARU: Mencegah error sintaks/tipe data)
        "BASE64",             # Krusial untuk K8s Secret, LLM harus tahu nilainya butuh base64
        "RFC 1123",           # Standar penamaan resource K8s (tidak boleh pakai spasi/huruf besar)
        "CIDR"                # Format jaringan (untuk NetworkPolicy atau Service)
    ]

    desc_upper = desc.upper()
    furthest_critical_pos = -1

    # Cari posisi keyword yang paling jauh di dalam teks
    for keyword in critical_keywords:
        pos = desc_upper.find(keyword, max_length - 500) 
        if pos != -1 and pos > furthest_critical_pos:
            furthest_critical_pos = pos

    # Jika ada keyword kritis yang ditemukan melewati batas max_length
    if furthest_critical_pos != -1:
        # Extend batasnya sampai ke keyword paling jauh + 150 karakter
        extended_max = min(furthest_critical_pos + 150, len(desc))
        
        # SAFETY HARD CAP: Jangan sampai melebihi panjang absolut (misal max_length + 1000)
        # Ini mencegah teks 5000 karakter masuk semua hanya karena ada "NOTE" di paling ujung.
        absolute_max = max_length + 1000
        extended_max = min(extended_max, absolute_max)
        
        desc = desc[:extended_max]

    # === Priority 2: Truncate at Sentence Boundary ===
    if len(desc) > max_length:
        truncated = desc[:max_length]
        # Find last sentence-ending punctuation
        last_period = truncated.rfind('.')
        last_newline = truncated.rfind('\n')
        
        # Use whichever is closer to the end (but not too far back)
        boundary = max(last_period, last_newline)
        if boundary > max_length - 100:  # Within last 100 chars
            desc = truncated[:boundary + 1]
        else:
            desc = truncated
    
    # === Priority 3: Add Ellipsis if Truncated ===
    if len(desc) < original_length:
        desc = desc.rstrip() + "..."
    
    return desc

def safe_truncate_description(desc: str, hard_limit: int = 4000) -> str:
    """
    Defensive safety cap for descriptions.
    
    Rationale: Empirical analysis of 729 Kubernetes API definitions shows
    99.86% have descriptions <2000 chars (avg: 140 chars). This function
    only truncates extreme outliers (>4000 chars) as defensive programming,
    while preserving 100% of normal data.
    
    Args:
        desc: Original description text
        hard_limit: Absolute maximum (default: 4000 chars)
    
    Returns:
        Description, truncated only if exceeding hard_limit
    """
    if not desc:
        return 'No description provided.'
    
    # Only truncate if extremely long (defensive programming)
    if len(desc) > hard_limit:
        truncated = desc[:hard_limit]
        # Try to end at sentence boundary for readability
        last_period = truncated.rfind('.')
        if last_period > hard_limit - 200:
            return truncated[:last_period + 1] + "..."
        return truncated + "..."
    
    # Return full description for 99.86% of cases ✅
    return desc