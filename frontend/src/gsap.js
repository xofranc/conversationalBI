import gsap from "gsap";

// Configuración global de GSAP para mejor rendimiento
gsap.config({
  force3D: true,
});

// Exportar GSAP para uso en scripts modulares
export default gsap;