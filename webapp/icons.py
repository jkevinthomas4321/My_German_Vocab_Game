"""Line icons for the four modes, as inline SVG (they take their colour from the surrounding text colour)."""

_OPEN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'

ICONS = {
    "learn": _OPEN + '<path d="M3.5 5.5c3-1.2 6-.8 8.5.9 2.5-1.7 5.5-2.1 8.5-.9v13c-3-1.2-6-.8-8.5.9-2.5-1.7-5.5-2.1-8.5-.9z"/><path d="M12 6.4v13"/></svg>',
    "test": _OPEN + '<rect x="4" y="3.5" width="16" height="17" rx="3"/><path d="M8.2 12.4l2.7 2.7 5-5.6"/></svg>',
    "second": _OPEN + '<path d="M4.6 12a7.4 7.4 0 1 0 2.3-5.4"/><path d="M4 4.2v4.6h4.6"/></svg>',
    "stay": _OPEN + '<rect x="5" y="3" width="14" height="18" rx="2.2"/><path d="M9.2 3v18M12.8 8h3.4M12.8 12h3.4"/></svg>',
}
