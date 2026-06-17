// Jeu d'icônes inline (stroke unique, style Lucide). Pas de dépendance externe.
const base = { width: 18, height: 18, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.7, strokeLinecap: "round", strokeLinejoin: "round" };

export const IconDash = (p) => (<svg {...base} {...p}><rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/></svg>);
export const IconPlus = (p) => (<svg {...base} {...p}><path d="M12 5v14M5 12h14"/></svg>);
export const IconUpdates = (p) => (<svg {...base} {...p}><path d="M12 3v12m0 0 4-4m-4 4-4-4"/><path d="M5 21h14"/></svg>);
export const IconMotd = (p) => (<svg {...base} {...p}><rect x="3" y="4" width="18" height="14" rx="2"/><path d="m7 9 2.5 2L7 13"/><path d="M12.5 13H17"/></svg>);
export const IconSettings = (p) => (<svg {...base} {...p}><path d="M4 6h10M18 6h2M4 12h2M10 12h10M4 18h7M15 18h5"/><circle cx="16" cy="6" r="2"/><circle cx="8" cy="12" r="2"/><circle cx="13" cy="18" r="2"/></svg>);
export const IconServer = (p) => (<svg {...base} {...p}><rect x="3" y="4" width="18" height="7" rx="2"/><rect x="3" y="13" width="18" height="7" rx="2"/><path d="M7 7.5h.01M7 16.5h.01"/></svg>);
export const IconChevron = (p) => (<svg {...base} {...p}><path d="m9 6 6 6-6 6"/></svg>);
export const IconExternal = (p) => (<svg {...base} {...p}><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg>);
export const IconCheck = (p) => (<svg {...base} {...p}><path d="M5 13l4 4L19 7"/></svg>);
export const IconRefresh = (p) => (<svg {...base} {...p}><path d="M21 12a9 9 0 1 1-3-6.7L21 8"/><path d="M21 4v4h-4"/></svg>);
export const IconTrash = (p) => (<svg {...base} {...p}><path d="M4 7h16M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2M6 7l1 13a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1l1-13"/></svg>);
export const IconSync = (p) => (<svg {...base} {...p}><path d="M4 9a8 8 0 0 1 14-3l2 2M20 15a8 8 0 0 1-14 3l-2-2"/><path d="M20 4v4h-4M4 20v-4h4"/></svg>);
export const IconBolt = (p) => (<svg {...base} {...p}><path d="M13 3 4 14h7l-1 7 9-11h-7l1-7Z"/></svg>);
