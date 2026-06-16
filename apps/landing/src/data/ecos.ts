export type EcoCategory = 'Reflexión' | 'Bioética' | 'Ciencia' | 'Magisterio' | 'Fertilidad';

export interface Eco {
  id: string;
  title: string;
  category: EcoCategory;
  duration: string;
  date: string;
}

export const categories: EcoCategory[] = ['Reflexión', 'Bioética', 'Ciencia', 'Magisterio', 'Fertilidad'];

export const ecos: Eco[] = [
  // — Reflexión —
  {
    id: "ref-01",
    title: "El silencio donde comienza la vida",
    category: "Reflexión",
    duration: "5:12",
    date: "Mayo 2026",
  },
  {
    id: "ref-02",
    title: "Carta a un hijo que aún no nace",
    category: "Reflexión",
    duration: "4:38",
    date: "Abril 2026",
  },
  {
    id: "ref-03",
    title: "Cuando el miedo habla más fuerte que el amor",
    category: "Reflexión",
    duration: "6:05",
    date: "Marzo 2026",
  },

  // — Bioética —
  {
    id: "bio-01",
    title: "Dignidad humana y decisiones médicas",
    category: "Bioética",
    duration: "7:22",
    date: "Junio 2026",
  },
  {
    id: "bio-02",
    title: "El embrión: persona o proyecto de persona",
    category: "Bioética",
    duration: "6:47",
    date: "Mayo 2026",
  },
  {
    id: "bio-03",
    title: "Consentimiento informado y maternidad vulnerable",
    category: "Bioética",
    duration: "5:33",
    date: "Abril 2026",
  },

  // — Ciencia —
  {
    id: "cie-01",
    title: "ADN único desde la concepción: lo que dice la genética",
    category: "Ciencia",
    duration: "4:55",
    date: "Junio 2026",
  },
  {
    id: "cie-02",
    title: "El latido fetal: cronología y evidencia científica",
    category: "Ciencia",
    duration: "5:18",
    date: "Mayo 2026",
  },
  {
    id: "cie-03",
    title: "Desarrollo neurológico prenatal: preguntas y respuestas",
    category: "Ciencia",
    duration: "7:41",
    date: "Marzo 2026",
  },

  // — Magisterio —
  {
    id: "mag-01",
    title: "Evangelium Vitae: el evangelio de la vida hoy",
    category: "Magisterio",
    duration: "6:10",
    date: "Junio 2026",
  },
  {
    id: "mag-02",
    title: "Papa Francisco y la cultura del descarte",
    category: "Magisterio",
    duration: "5:44",
    date: "Abril 2026",
  },
  {
    id: "mag-03",
    title: "Humanae Vitae: profecía y actualidad",
    category: "Magisterio",
    duration: "7:58",
    date: "Febrero 2026",
  },

  // — Fertilidad —
  {
    id: "fer-01",
    title: "Conocer tu fertilidad: introducción a los métodos naturales",
    category: "Fertilidad",
    duration: "4:29",
    date: "Junio 2026",
  },
  {
    id: "fer-02",
    title: "Método sintotérmico: ciencia al servicio del amor",
    category: "Fertilidad",
    duration: "6:33",
    date: "Mayo 2026",
  },
  {
    id: "fer-03",
    title: "Fertilidad y proyecto de vida: más allá de la anticoncepción",
    category: "Fertilidad",
    duration: "3:52",
    date: "Abril 2026",
  },
];
