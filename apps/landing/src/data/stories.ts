export interface Story {
  slug: string;
  name: string;
  age?: string;
  place: string;
  headline: string;
  excerpt: string;
  cover: string;
  portrait: string;
  date: string;
  readingTime: string;
  category: string;
  body: string[];
}

export const stories: Story[] = [
  {
    slug: "maria-buenos-aires",
    name: "María",
    age: "22 años",
    place: "Buenos Aires, Argentina",
    headline: "Estaba sola y asustada. Hoy mi hija es mi razón de vivir.",
    excerpt:
      "Cuando descubrí que estaba embarazada, lo primero que sentí fue miedo. Mis amigas me decían que no arruinara mi vida. Hasta que una voz distinta me escuchó sin juzgar.",
    cover: "/images/img-19.webp",
    portrait: "/images/img-19.webp",
    date: "Marzo 2026",
    readingTime: "5 min de lectura",
    category: "Madres acompañadas",
    body: [
      "Tenía 19 años cuando hice el test. Lo recuerdo como si fuera ayer: dos líneas rojas y todo el mundo girando demasiado rápido. Estaba estudiando, vivía con una amiga, y mi novio había desaparecido del mapa hacía semanas.",
      "Mis primeras llamadas fueron a las personas equivocadas. \"No te compliques\", me decían. \"Ahora se puede, es rápido.\" Por un momento les creí. El miedo te empuja a soluciones que después no podés deshacer.",
      "Una compañera de la facultad me habló de IAM. No prometieron nada milagroso. Solo me ofrecieron una tarde para charlar. Esa tarde se convirtió en un acompañamiento de meses: una psicóloga, una abogada, una familia que me hospedó cuando mis padres me echaron.",
      "Sofía nació en abril. Hoy tiene 3 años y le encanta cantar. Cada vez que la escucho dormirse pienso en aquella tarde y agradezco que alguien me haya escuchado sin juzgar. No me dijeron qué hacer. Me ayudaron a descubrir que yo podía.",
      "Si hoy estás leyendo esto y tenés miedo: no estás sola. Hay puertas que se abren cuando creés que todas están cerradas. La mía se llamó IAM.",
    ],
  },
  {
    slug: "carolina-lima",
    name: "Carolina",
    age: "28 años",
    place: "Lima, Perú",
    headline: "Me dijeron que mi bebé no era viable. Hoy él es mi milagro.",
    excerpt:
      "Tres médicos coincidieron: \"Interrumpir es la opción más humana.\" Decidí buscar una cuarta opinión. Y luego una quinta. Y luego decidí escuchar mi corazón.",
    cover: "/images/img-12.webp",
    portrait: "/images/img-12.webp",
    date: "Enero 2026",
    readingTime: "6 min de lectura",
    category: "Diagnóstico difícil",
    body: [
      "A las 20 semanas nos dijeron que algo no estaba bien. Las palabras médicas son frías cuando lo que estás escuchando es sobre tu bebé. \"Malformación severa.\" \"Pronóstico reservado.\" \"Considere sus opciones.\"",
      "Mi esposo y yo lloramos esa noche hasta quedarnos sin lágrimas. Al día siguiente empezamos a buscar más opiniones. No por terquedad: por amor.",
      "IAM nos conectó con médicos que tratan estos casos, con familias que habían pasado por lo mismo, con un sacerdote que escuchó nuestras dudas más oscuras sin asustarse.",
      "Mateo nació con desafíos, sí. También nació con una sonrisa que ilumina cualquier habitación. Tiene 4 años y nos enseña cada día qué significa la palabra dignidad.",
      "No todas las historias terminan en finales perfectos según el manual del mundo. Pero todas las vidas merecen ser recibidas con amor. La nuestra es una prueba.",
    ],
  },
  {
    slug: "familia-lopez",
    name: "Familia López",
    place: "Ciudad de México",
    headline: "Adoptamos a Lucía. Ella nos eligió antes de nacer.",
    excerpt:
      "Después de años intentando, encontramos otro camino. Hoy somos tres y entendemos que la familia no se construye con sangre: se construye con sí.",
    cover: "/images/img-04.webp",
    portrait: "/images/img-04.webp",
    date: "Noviembre 2025",
    readingTime: "4 min de lectura",
    category: "Adopción",
    body: [
      "Después de cinco años de tratamientos, mi esposo y yo decidimos que era hora de mirar hacia otro lado. La adopción siempre estuvo en nuestra mente, pero nos asustaba el proceso.",
      "IAM tiene un programa que conecta a madres en crisis con familias dispuestas a adoptar. Nos prepararon emocional, legal y espiritualmente durante meses.",
      "Conocimos a Daniela cuando estaba embarazada de seis meses. Ella había decidido continuar con el embarazo y dar a su bebé en adopción. Nos eligió entre varias familias.",
      "El día que nació Lucía estuvimos en el hospital. Daniela nos la puso en los brazos y dijo: \"Cuídenla como yo no puedo, pero quiéranla por las dos.\"",
      "Hoy Lucía tiene 2 años. Daniela es parte de nuestra familia extendida: la vemos en cumpleaños y navidades. Eligió la vida dos veces: la de Lucía y la nuestra como familia.",
    ],
  },
  {
    slug: "diego-bogota",
    name: "Diego",
    age: "23 años",
    place: "Bogotá, Colombia",
    headline: "Empecé a los 14 años. Hoy soy misionero a tiempo completo.",
    excerpt:
      "Mi catequista me llevó a un retiro de IAM cuando tenía 14. No imaginé que esa decisión iba a definir el resto de mi vida.",
    cover: "/images/img-43.webp",
    portrait: "/images/img-43.webp",
    date: "Septiembre 2025",
    readingTime: "5 min de lectura",
    category: "Voluntarios",
    body: [
      "A los 14 yo era un chico común. Jugaba fútbol, peleaba con mis hermanas, me iba mal en matemática. Mi catequista insistió tanto que terminé yendo a un retiro de IAM solo para que dejara de molestarme.",
      "Lo que escuché ese fin de semana me cambió. No fue un sermón. Fueron historias reales: una madre adolescente que casi aborta, un médico que dejó su clínica porque no quería seguir interrumpiendo vidas, una pareja que recibió a un bebé con síndrome de Down.",
      "Volví a casa con preguntas. Y con ganas de ser parte. Empecé acompañando en jornadas escolares, hablando con compañeros sobre el valor de la vida desde mi propia experiencia.",
      "A los 18 entré a formación más profunda. Hoy, a los 23, coordino el área de jóvenes en Colombia. Estudio Psicología en paralelo porque entiendo que esta misión necesita herramientas concretas.",
      "Si tenés entre 12 y 18 años y estás leyendo esto: no creas que sos demasiado joven para cambiar algo. Yo lo era. Y aquí estamos.",
    ],
  },
];
