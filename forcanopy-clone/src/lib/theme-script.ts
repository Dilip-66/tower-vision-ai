/**
 * Applies the persisted theme before first paint so there is no flash of the
 * wrong palette. Mirrors the inline script the reference build ships.
 */
export const THEME_INIT_SCRIPT = `(function(){try{var t=localStorage.getItem('theme');if(t==='dark'||t==='light'){document.documentElement.setAttribute('data-theme',t);}}catch(e){}})();`;
