import hashlib


def get_avatar_color(username):
    """Generate consistent color from username hash"""
    hash_obj = hashlib.md5(username.encode())
    hash_hex = hash_obj.hexdigest()
    
    # Predefined color palette for consistency
    colors = [
        "#667eea", "#764ba2", "#f093fb", "#4facfe", "#43e97b",
        "#fa709a", "#fee140", "#30cfd0", "#a8edea", "#fed6e3"
    ]
    
    # Use hash to pick a color
    color_index = int(hash_hex, 16) % len(colors)
    return colors[color_index]


def get_avatar_initials(username):
    """Get first letter of username (uppercase)"""
    return username[0].upper() if username else "?"


def render_avatar_html(username, size="40px"):
    """Generate HTML for avatar badge"""
    initials = get_avatar_initials(username)
    color = get_avatar_color(username)
    
    return f"""
    <div style="
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: {size};
        height: {size};
        border-radius: 50%;
        background: {color};
        color: white;
        font-weight: bold;
        font-size: calc({size} * 0.5);
        font-family: Arial, sans-serif;
        cursor: pointer;
        user-select: none;
    ">
        {initials}
    </div>
    """
