// Langage de motion partagé — une seule courbe, une seule logique d'entrée.
// Sobre et fonctionnel : guider l'œil, pas décorer.

export const EASE = [0.16, 1, 0.3, 1];

// Conteneur qui orchestre l'apparition de ses enfants en cascade.
export const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.05, delayChildren: 0.04 } },
};

// Élément qui monte légèrement en apparaissant.
export const riseItem = {
  hidden: { opacity: 0, y: 10 },
  show: { opacity: 1, y: 0, transition: { duration: 0.34, ease: EASE } },
};

// Transition entre routes.
export const pageVariants = {
  initial: { opacity: 0, y: 8 },
  enter: { opacity: 1, y: 0, transition: { duration: 0.28, ease: EASE } },
  exit: { opacity: 0, y: -6, transition: { duration: 0.16, ease: EASE } },
};

// Lift au survol des tuiles bento.
export const tileHover = {
  rest: { y: 0 },
  hover: { y: -3, transition: { duration: 0.18, ease: EASE } },
};
