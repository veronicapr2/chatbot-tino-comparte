const API_URL = window.TINO_BACKEND_URL ||
    (window.location.port === "5000"
        ? "/chat"
        : "http://127.0.0.1:5000/chat");const TINO_IMAGE = "/img/Tino3.png";
const TINO_DEBUG = window.TINO_DEBUG === true || localStorage.getItem("tinoDebug") === "true";

let enviando = false;

const HISTORY_KEY = "tinoChatHistory";const CURRENT_CHAT_KEY = "tinoCurrentChatId";const DARK_MODE_KEY = "modoOscuro";const LANGUAGE_KEY = "idiomaChatbot";const FONT_SIZE_KEY = "tinoFontSize";const GRAYSCALE_KEY = "tinoGrayscaleMode";

let reconocimientoVoz = null;let textoTranscritoFinal = "";let observadorAccesibilidad = null;let aplicandoEscalaTipografica = false;
let vocesLecturaBot = [];
let botonLecturaBotActivo = null;
let idLecturaBotActual = 0;

/* ========================================= // TEXTOS POR IDIOMA // ========================================= */

const textosIdioma = {

es: {
    welcomeTitleOne: "Chatea con",
    welcomeTitleTwo: "Tino",
    welcomeText: "Hola, soy Tino. Estoy listo para ayudarte. ¿En qué puedo apoyarte hoy?",
    startBtn: "Comenzar",

    sidebarSubtitle: "Asistente Virtual",
    sidebarHome: "Inicio",
    sidebarChat: "Chat IA",
    sidebarSettings: "Configuración",
    sidebarHistory: "Historial",
    sidebarSupport: "Ayuda y soporte",

    dashboardGreeting: "Hola,",
    dashboardName: "Soy Tino",
    dashboardSubtitle: "¿Cómo podemos ayudarte hoy?",
    quoteText: "Estamos aquí para ayudarte y mejorar tu experiencia.",

    featureChat: "Chat IA",
    featureChatDescription: "Habla con Tino y resuelve tus dudas.",
    featureTestimonials: "Testimonios",
    featureTestimonialsDescription: "Conoce lo que dicen otros usuarios.",

    faqTitle: "Preguntas frecuentes",
    faqOne: "¿Cómo funciona el Chat IA?",
    faqTwo: "¿Qué información puede proporcionarme Tino?",
    faqThree: "¿Cómo puedo enviar un testimonio?",
    faqFour: "¿Cuánto tiempo tarda en responder el Chat IA?",
    faqFive: "¿Mi información está segura?",

    notificationsTitle: "Notificaciones",
    notificationOne: "Nuevo documento agregado",
    notificationTwo: "Sistema IA optimizado",

    settingsTitle: "Configuración",
    darkModeTitle: "Modo oscuro",
    darkModeText: "Activa el tema oscuro para una experiencia más cómoda.",
    languageTitle: "Idioma",
    languageText: "Selecciona el idioma de la aplicación.",
    accessibilityTitle: "Accesibilidad",
    accessibilityText: "Ajusta la visualización del chatbot.",
    fontSizeTitle: "Tamaño de letra",
    fontSmall: "Pequeña",
    fontNormal: "Normal",
    fontLarge: "Grande",
    grayscaleTitle: "Escala de grises",

    historyTitle: "Historial",
    historySearch: "Buscar en el historial...",
    historySectionTitle: "Conversaciones recientes",
    clearHistory: "Eliminar todo el historial",
    emptyHistoryTitle: "No hay conversaciones aún",
    emptyHistoryText: "Cuando hables con Tino, tus conversaciones aparecerán aquí.",

    supportTitle: "Ayuda y soporte",
    supportSubtitle: "Estamos aquí para ayudarte ♡",
    supportEmailText: "Te responderemos lo antes posible",
    supportPhoneText: "Llámanos de lunes a viernes 8:00 a.m. – 6:00 p.m.",
    supportWebText: "Visita nuestro sitio web y conoce más sobre Latam Comparte",
    supportTinoTitle: "¡Hola! Soy Tino",
    supportTinoText: "Estoy aquí para ayudarte con lo que necesites.",
    supportTinoQuestion: "¿En qué puedo ayudarte hoy?",

    testimonialsTitle: "Testimonios",
    testimonialsSubtitle: "Historias reales en video",
    testimonialsIntroText: "Conoce las experiencias de personas que han transformado su vida con el apoyo de la comunidad.",
    testimonialsStoriesTitle: "Historias que inspiran",
    testimonialVideoOneTitle: "Un nuevo comienzo",
    testimonialVideoOneText: "Conoce cómo María encontró apoyo y herramientas para emprender su proyecto.",
    testimonialVideoOneName: "María G.",
    testimonialVideoTwoTitle: "Creciendo juntos",
    testimonialVideoTwoText: "La historia de Carlos y cómo la comunidad lo impulsó a alcanzar sus metas.",
    testimonialVideoTwoName: "Carlos R.",
    testimonialVideoThreeTitle: "Más que apoyo, familia",
    testimonialVideoThreeText: "Valeria comparte cómo encontró amistad, guía y crecimiento personal.",
    testimonialVideoThreeName: "Valeria T.",

    chatSubtitle: "Tu asistente virtual",
    onlineStatus: "● Online",
    inputPlaceholder: "Escribe tu pregunta...",
    botWelcome: "¡Hola! Soy Tino. ¿En qué puedo ayudarte hoy?",

    voiceTitle: "¡Hola amigo!",
    voiceSubtitle: "Haz tu pregunta por voz",
    voiceInstruction: "Presiona el micrófono y habla",
    voiceReady: "Tino está listo para escucharte...",
    voiceListening: "Tino está escuchando...",
    voiceStopped: "Grabación detenida.",
    voiceError: "No pude escuchar bien. Intenta de nuevo.",
    voiceUnsupported: "Tu navegador no soporta reconocimiento de voz. Usa Google Chrome o Edge.",
    voiceTranscriptPlaceholder: "Tu texto aparecerá aquí...",
    voiceListeningText: "Escuchando...",
    voiceStopButton: "Detener grabación",
    voiceUseTextButton: "Usar este texto",

    typing: "Tino está escribiendo...",
    invalidServer: "El servidor devolvió una respuesta inválida.",
    serverError: "Ocurrió un error en el servidor.",
    noResponse: "No recibí respuesta del servidor.",
    connectionError: "No pude conectarme con el servidor.",

    deleteConfirm: "¿Seguro que quieres eliminar todo el historial de conversaciones?",
    newConversation: "Nueva conversación",
    conversationStarted: "Conversación iniciada",

    curiosities: [
        {
            title: "¿Sabías que la fundación nació de una experiencia personal muy fuerte?",
            text: "Sus cofundadores, Carolina Ruiz Herrera y Eduardo Del Castillo, perdieron todo antes de crear el proyecto."
        },
        {
            title: "¿Por qué contratar a Colombia Comparte?",
            text: "Brinda compra incluyente, apoyo social, certificado de donación, profesionales reconocidos y Responsabilidad Social Corporativa."
        },
        {
            title: "¿Sabías que reconocemos el valor de las familias de los empleados?",
            text: "Fortalecemos la base de apoyo emocional de los colaboradores y fomentamos un ambiente laboral más comprometido y productivo."
        },
        {
            title: "¿Sabías que funcionamos bajo un modelo de organización social autosostenible?",
            text: "Combinamos impacto social con programas empresariales y de emprendimiento para sostener económicamente la organización."
        },
        {
            title: "¿Ya conocías los enfoques que apoyan tu idea de negocio?",
            text: "Trabajamos seis enfoques: emprendimiento, desarrollo, innovación, formación, crecimiento y aceleración."
        },
        {
            title: "¿Sabías que también ofrecemos Top Speakers?",
            text: "Este programa está pensado para dejar una marca imborrable en tu organización o grupo."
        },
        {
            title: "¿Sabías que Colombia Comparte brinda shows para eventos empresariales?",
            text: "Este servicio ofrece diversión garantizada, amplia variedad y personalización."
        },
        {
            title: "¿Sabías que hemos apoyado durante 9 años el programa Juntos - Familias Vergonzantes?",
            text: "Este acompañamiento se ha logrado a través del programa de altos estudios en emprendimiento EDIFICA."
        },
        {
            title: "¿Sabías que existe Latinoamérica Comparte?",
            text: "Lo que comenzó en Colombia hoy es una red continental que promueve bienestar, cultura organizacional y emprendimiento con propósito."
        },
        {
            title: "¿Sabías que puedes ayudar al objetivo de Latinoamérica Comparte?",
            text: "Puedes apoyar aliándote como empresa o realizando donaciones individuales."
        },
        {
            title: "¿Sabías que Latinoamérica Comparte tiene más de 40 empresas aliadas?",
            text: "Las empresas que creen en el bienestar y la productividad con propósito hacen parte de esta red."
        },
        {
            title: "¿Sabías que también hay otros países que comparten?",
            text: "Además de Colombia, existen Ecuador Comparte, Chile Comparte y Argentina Comparte."
        },
        {
            title: "¿Sabías que algunos programas apoyan a mujeres cabeza de hogar?",
            text: "También acompañamos a familias afectadas por crisis económicas recientes."
        },
        {
            title: "¿Sabías que Latinoamérica Comparte también trabaja el bienestar emocional?",
            text: "No se enfoca solo en productividad económica, también fortalece el propósito dentro de las empresas."
        },
        {
            title: "¿Sabías que existe un Directorio de Emprendedores?",
            text: "La idea es visibilizar y conectar negocios creados o fortalecidos por personas apoyadas por la fundación."
        }
    ]
},

en: {
    welcomeTitleOne: "Chat with",
    welcomeTitleTwo: "Tino",
    welcomeText: "Hi, I’m Tino. I’m ready to help you. How can I support you today?",
    startBtn: "Start",

    sidebarSubtitle: "Virtual Assistant",
    sidebarHome: "Home",
    sidebarChat: "AI Chat",
    sidebarSettings: "Settings",
    sidebarHistory: "History",
    sidebarSupport: "Help and support",

    dashboardGreeting: "Hi,",
    dashboardName: "I’m Tino",
    dashboardSubtitle: "How can we help you today?",
    quoteText: "We are here to help you and improve your experience.",

    featureChat: "AI Chat",
    featureChatDescription: "Talk to Tino and solve your questions.",
    featureTestimonials: "Testimonials",
    featureTestimonialsDescription: "See what other users say.",

    faqTitle: "Frequently Asked Questions",
    faqOne: "How does the AI Chat work?",
    faqTwo: "What information can Tino provide?",
    faqThree: "How can I send a testimonial?",
    faqFour: "How long does the AI Chat take to respond?",
    faqFive: "Is my information safe?",

    notificationsTitle: "Notifications",
    notificationOne: "New document added",
    notificationTwo: "AI system optimized",

    settingsTitle: "Settings",
    darkModeTitle: "Dark mode",
    darkModeText: "Enable dark theme for a more comfortable experience.",
    languageTitle: "Language",
    languageText: "Select the application language.",
    accessibilityTitle: "Accessibility",
    accessibilityText: "Adjust the chatbot display.",
    fontSizeTitle: "Font size",
    fontSmall: "Small",
    fontNormal: "Normal",
    fontLarge: "Large",
    grayscaleTitle: "Grayscale",

    historyTitle: "History",
    historySearch: "Search history...",
    historySectionTitle: "Recent conversations",
    clearHistory: "Delete all history",
    emptyHistoryTitle: "No conversations yet",
    emptyHistoryText: "When you talk to Tino, your conversations will appear here.",

    supportTitle: "Help and support",
    supportSubtitle: "We are here to help you ♡",
    supportEmailText: "We will reply as soon as possible",
    supportPhoneText: "Call us Monday to Friday 8:00 a.m. – 6:00 p.m.",
    supportWebText: "Visit our website and learn more about Latam Comparte",
    supportTinoTitle: "Hi! I’m Tino",
    supportTinoText: "I’m here to help you with whatever you need.",
    supportTinoQuestion: "How can I help you today?",

    testimonialsTitle: "Testimonials",
    testimonialsSubtitle: "Real stories in video",
    testimonialsIntroText: "Discover the experiences of people who have transformed their lives with community support.",
    testimonialsStoriesTitle: "Inspiring stories",
    testimonialVideoOneTitle: "A new beginning",
    testimonialVideoOneText: "See how María found support and tools to start her project.",
    testimonialVideoOneName: "María G.",
    testimonialVideoTwoTitle: "Growing together",
    testimonialVideoTwoText: "Carlos’ story and how the community helped him reach his goals.",
    testimonialVideoTwoName: "Carlos R.",
    testimonialVideoThreeTitle: "More than support, family",
    testimonialVideoThreeText: "Valeria shares how she found friendship, guidance and personal growth.",
    testimonialVideoThreeName: "Valeria T.",

    chatSubtitle: "Your virtual assistant",
    onlineStatus: "● Online",
    inputPlaceholder: "Type your question...",
    botWelcome: "Hi! I’m Tino. How can I help you today?",

    voiceTitle: "Hi Friend!",
    voiceSubtitle: "Ask your question by voice",
    voiceInstruction: "Press the microphone and speak",
    voiceReady: "Tino is ready to listen...",
    voiceListening: "Tino is listening...",
    voiceStopped: "Recording stopped.",
    voiceError: "I could not hear you clearly. Try again.",
    voiceUnsupported: "Your browser does not support voice recognition. Use Google Chrome or Edge.",
    voiceTranscriptPlaceholder: "Your text will appear here...",
    voiceListeningText: "Listening...",
    voiceStopButton: "Stop recording",
    voiceUseTextButton: "Use this text",

    typing: "Tino is typing...",
    invalidServer: "The server returned an invalid response.",
    serverError: "A server error occurred.",
    noResponse: "I did not receive a response from the server.",
    connectionError: "I could not connect to the server.",

    deleteConfirm: "Are you sure you want to delete all chat history?",
    newConversation: "New conversation",
    conversationStarted: "Conversation started",

    curiosities: [
        {
            title: "Did you know the foundation was born from a very strong personal experience?",
            text: "Its co-founders, Carolina Ruiz Herrera and Eduardo Del Castillo, lost everything before creating the project."
        },
        {
            title: "Why work with Colombia Comparte?",
            text: "It offers inclusive purchasing, social support, donation certificates, recognized professionals and Corporate Social Responsibility."
        },
        {
            title: "Did you know we recognize the value of employees’ families?",
            text: "We strengthen employees’ emotional support network and promote a more committed and productive work environment."
        },
        {
            title: "Did you know we operate under a self-sustaining social organization model?",
            text: "We combine social impact with business and entrepreneurship programs to financially sustain the organization."
        },
        {
            title: "Did you know the approaches that support your business idea?",
            text: "We work with six approaches: entrepreneurship, development, innovation, training, growth and acceleration."
        },
        {
            title: "Did you know we also offer Top Speakers?",
            text: "This program is designed to leave a lasting mark on your organization or group."
        },
        {
            title: "Did you know Colombia Comparte offers shows for corporate events?",
            text: "This service offers guaranteed fun, variety and personalization."
        },
        {
            title: "Did you know we have supported Juntos - Familias Vergonzantes for 9 years?",
            text: "This support has been provided through the advanced entrepreneurship studies program EDIFICA."
        },
        {
            title: "Did you know Latinoamérica Comparte exists?",
            text: "What began in Colombia is now a continental network that promotes well-being, organizational culture and purpose-driven entrepreneurship."
        },
        {
            title: "Did you know you can support Latinoamérica Comparte’s mission?",
            text: "You can support by becoming a business ally or by making individual donations."
        },
        {
            title: "Did you know Latinoamérica Comparte has more than 40 partner companies?",
            text: "Companies that believe in well-being and purpose-driven productivity are part of this network."
        },
        {
            title: "Did you know other countries also share?",
            text: "In addition to Colombia, there are Ecuador Comparte, Chile Comparte and Argentina Comparte."
        },
        {
            title: "Did you know some programs support women heads of household?",
            text: "We also support families affected by recent economic crises."
        },
        {
            title: "Did you know Latinoamérica Comparte also works on emotional well-being?",
            text: "It does not focus only on economic productivity; it also strengthens purpose within companies."
        },
        {
            title: "Did you know there is an Entrepreneurs Directory?",
            text: "The goal is to make visible and connect businesses created or strengthened by people supported by the foundation."
        }
    ]
},

pt: {
    welcomeTitleOne: "Converse com",
    welcomeTitleTwo: "Tino",
    welcomeText: "Olá, sou o Tino. Estou pronto para ajudar você. Como posso apoiar você hoje?",
    startBtn: "Começar",

    sidebarSubtitle: "Assistente Virtual",
    sidebarHome: "Início",
    sidebarChat: "Chat IA",
    sidebarSettings: "Configuração",
    sidebarHistory: "Histórico",
    sidebarSupport: "Ajuda e suporte",

    dashboardGreeting: "Olá,",
    dashboardName: "Sou Tino",
    dashboardSubtitle: "Como podemos ajudar você hoje?",
    quoteText: "Estamos aqui para ajudar você e melhorar sua experiência.",

    featureChat: "Chat IA",
    featureChatDescription: "Fale com Tino e tire suas dúvidas.",
    featureTestimonials: "Depoimentos",
    featureTestimonialsDescription: "Veja o que outros usuários dizem.",

    faqTitle: "Perguntas frequentes",
    faqOne: "Como funciona o Chat IA?",
    faqTwo: "Que informações Tino pode fornecer?",
    faqThree: "Como posso enviar um depoimento?",
    faqFour: "Quanto tempo o Chat IA demora para responder?",
    faqFive: "Minhas informações estão seguras?",

    notificationsTitle: "Notificações",
    notificationOne: "Novo documento adicionado",
    notificationTwo: "Sistema IA otimizado",

    settingsTitle: "Configuração",
    darkModeTitle: "Modo escuro",
    darkModeText: "Ative o tema escuro para uma experiência mais confortável.",
    languageTitle: "Idioma",
    languageText: "Selecione o idioma do aplicativo.",
    accessibilityTitle: "Acessibilidade",
    accessibilityText: "Ajuste a visualização do chatbot.",
    fontSizeTitle: "Tamanho da letra",
    fontSmall: "Pequena",
    fontNormal: "Normal",
    fontLarge: "Grande",
    grayscaleTitle: "Escala de cinza",

    historyTitle: "Histórico",
    historySearch: "Pesquisar no histórico...",
    historySectionTitle: "Conversas recentes",
    clearHistory: "Excluir todo o histórico",
    emptyHistoryTitle: "Ainda não há conversas",
    emptyHistoryText: "Quando você falar com Tino, suas conversas aparecerão aqui.",

    supportTitle: "Ajuda e suporte",
    supportSubtitle: "Estamos aqui para ajudar você ♡",
    supportEmailText: "Responderemos o mais breve possível",
    supportPhoneText: "Ligue de segunda a sexta 8:00 a.m. – 6:00 p.m.",
    supportWebText: "Visite nosso site e saiba mais sobre Latam Comparte",
    supportTinoTitle: "Olá! Sou o Tino",
    supportTinoText: "Estou aqui para ajudar você com o que precisar.",
    supportTinoQuestion: "Como posso ajudar você hoje?",

    testimonialsTitle: "Depoimentos",
    testimonialsSubtitle: "Histórias reais em vídeo",
    testimonialsIntroText: "Conheça as experiências de pessoas que transformaram suas vidas com o apoio da comunidade.",
    testimonialsStoriesTitle: "Histórias que inspiram",
    testimonialVideoOneTitle: "Um novo começo",
    testimonialVideoOneText: "Veja como María encontrou apoio e ferramentas para iniciar seu projeto.",
    testimonialVideoOneName: "María G.",
    testimonialVideoTwoTitle: "Crescendo juntos",
    testimonialVideoTwoText: "A história de Carlos e como a comunidade o ajudou a alcançar suas metas.",
    testimonialVideoTwoName: "Carlos R.",
    testimonialVideoThreeTitle: "Mais que apoio, família",
    testimonialVideoThreeText: "Valeria compartilha como encontrou amizade, orientação e crescimento pessoal.",
    testimonialVideoThreeName: "Valeria T.",

    chatSubtitle: "Seu assistente virtual",
    onlineStatus: "● Online",
    inputPlaceholder: "Digite sua pergunta...",
    botWelcome: "Olá! Sou o Tino. Como posso ajudar você hoje?",

    voiceTitle: "Oi Amigo!",
    voiceSubtitle: "Faça sua pergunta por voz",
    voiceInstruction: "Pressione o microfone e fale",
    voiceReady: "Tino está pronto para ouvir você...",
    voiceListening: "Tino está ouvindo...",
    voiceStopped: "Gravação parada.",
    voiceError: "Não consegui ouvir bem. Tente novamente.",
    voiceUnsupported: "Seu navegador não suporta reconhecimento de voz. Use Google Chrome ou Edge.",
    voiceTranscriptPlaceholder: "Seu texto aparecerá aqui...",
    voiceListeningText: "Ouvindo...",
    voiceStopButton: "Parar gravação",
    voiceUseTextButton: "Usar este texto",

    typing: "Tino está escrevendo...",
    invalidServer: "O servidor retornou uma resposta inválida.",
    serverError: "Ocorreu um erro no servidor.",
    noResponse: "Não recebi resposta do servidor.",
    connectionError: "Não consegui me conectar ao servidor.",

    deleteConfirm: "Tem certeza de que deseja excluir todo o histórico de conversas?",
    newConversation: "Nova conversa",
    conversationStarted: "Conversa iniciada",

    curiosities: [
        {
            title: "Você sabia que a fundação nasceu de uma experiência pessoal muito forte?",
            text: "Seus cofundadores, Carolina Ruiz Herrera e Eduardo Del Castillo, perderam tudo antes de criar o projeto."
        },
        {
            title: "Por que contratar a Colombia Comparte?",
            text: "Oferece compra inclusiva, apoio social, certificado de doação, profissionais reconhecidos e Responsabilidade Social Corporativa."
        },
        {
            title: "Você sabia que reconhecemos o valor das famílias dos colaboradores?",
            text: "Fortalecemos a base de apoio emocional dos colaboradores e promovemos um ambiente de trabalho mais comprometido e produtivo."
        },
        {
            title: "Você sabia que funcionamos sob um modelo de organização social autossustentável?",
            text: "Combinamos impacto social com programas empresariais e de empreendedorismo para sustentar economicamente a organização."
        },
        {
            title: "Você já conhecia os enfoques que apoiam sua ideia de negócio?",
            text: "Trabalhamos seis enfoques: empreendedorismo, desenvolvimento, inovação, formação, crescimento e aceleração."
        },
        {
            title: "Você sabia que também oferecemos Top Speakers?",
            text: "Este programa foi pensado para deixar uma marca inesquecível em sua organização ou grupo."
        },
        {
            title: "Você sabia que a Colombia Comparte oferece shows para eventos empresariais?",
            text: "Este serviço oferece diversão garantida, ampla variedade e personalização."
        },
        {
            title: "Você sabia que apoiamos há 9 anos o programa Juntos - Familias Vergonzantes?",
            text: "Esse acompanhamento foi realizado por meio do programa de altos estudos em empreendedorismo EDIFICA."
        },
        {
            title: "Você sabia que existe a Latinoamérica Comparte?",
            text: "O que começou na Colômbia hoje é uma rede continental que promove bem-estar, cultura organizacional e empreendedorismo com propósito."
        },
        {
            title: "Você sabia que pode apoiar o objetivo da Latinoamérica Comparte?",
            text: "Você pode apoiar tornando-se uma empresa aliada ou realizando doações individuais."
        },
        {
            title: "Você sabia que a Latinoamérica Comparte tem mais de 40 empresas aliadas?",
            text: "As empresas que acreditam no bem-estar e na produtividade com propósito fazem parte desta rede."
        },
        {
            title: "Você sabia que outros países também compartilham?",
            text: "Além da Colômbia, existem Ecuador Comparte, Chile Comparte e Argentina Comparte."
        },
        {
            title: "Você sabia que alguns programas apoiam mulheres chefes de família?",
            text: "Também acompanhamos famílias afetadas por crises econômicas recentes."
        },
        {
            title: "Você sabia que a Latinoamérica Comparte também trabalha o bem-estar emocional?",
            text: "Não se concentra apenas na produtividade econômica; também fortalece o propósito dentro das empresas."
        },
        {
            title: "Você sabia que existe um Diretório de Empreendedores?",
            text: "A ideia é dar visibilidade e conectar negócios criados ou fortalecidos por pessoas apoiadas pela fundação."
        }
    ]
}

};

/* ========================================= // UTILIDADES // ========================================= */

function obtenerIdiomaActual() {return localStorage.getItem(LANGUAGE_KEY) || "es";}

function obtenerTextos() {const idioma = obtenerIdiomaActual();return textosIdioma[idioma] || textosIdioma.es;}

const CONFIG_LECTURA_BOT = {
    es: {
        lang: "es-CO",
        fallbacks: ["es-CO", "es-MX", "es-US", "es-419", "es-AR", "es-CL", "es-PE", "es"],
        avoidedLangs: ["es-ES"],
        preferredTerms: [
            "natural",
            "neural",
            "online",
            "google",
            "microsoft",
            "soft",
            "suave",
            "friendly",
            "joven",
            "chico",
            "colombia",
            "colombian",
            "mexico",
            "mexican",
            "latam",
            "latin",
            "latino",
            "latinoamerica",
            "latin america",
            "estados unidos",
            "united states",
            "alvaro",
            "gonzalo",
            "lorenzo",
            "salvador",
            "raul"
        ],
        avoidedTerms: ["castilian", "castellano", "spain", "espana", "es-es", "helena", "compact", "legacy", "desktop", "robot"],
        rate: 0.91,
        pitch: 1.14,
        listenLabel: "Escuchar respuesta",
        stopLabel: "Detener lectura",
        unsupportedLabel: "Lectura de voz no disponible"
    },
    en: {
        lang: "en-US",
        fallbacks: ["en-US", "en-CA", "en-AU", "en-GB", "en"],
        avoidedLangs: [],
        preferredTerms: [
            "united states",
            "us english",
            "andrew",
            "brandon",
            "christopher",
            "guy",
            "tony"
        ],
        avoidedTerms: [],
        rate: 0.94,
        pitch: 1.07,
        listenLabel: "Listen to response",
        stopLabel: "Stop reading",
        unsupportedLabel: "Voice reading is not available"
    },
    pt: {
        lang: "pt-BR",
        fallbacks: ["pt-BR", "pt", "pt-PT"],
        avoidedLangs: ["pt-PT"],
        preferredTerms: [
            "brasil",
            "brazil",
            "antonio",
            "daniel",
            "thiago",
            "lucas",
            "fabricio"
        ],
        avoidedTerms: ["portugal", "pt-pt"],
        rate: 0.92,
        pitch: 1.08,
        listenLabel: "Ouvir resposta",
        stopLabel: "Parar leitura",
        unsupportedLabel: "Leitura de voz indisponivel"
    }
};

const TERMINOS_VOZ_MASCULINA = [
    "male",
    "man",
    "masculino",
    "hombre",
    "boy",
    "chico",
    "joven",
    "young",
    "daniel",
    "diego",
    "jorge",
    "carlos",
    "miguel",
    "antonio",
    "felipe",
    "joao",
    "thiago",
    "lucas"
];

const TERMINOS_VOZ_AMABLE = [
    "natural",
    "neural",
    "premium",
    "enhanced",
    "clear",
    "clara",
    "claro",
    "soft",
    "suave",
    "gentle",
    "calm",
    "warm",
    "sweet",
    "dulce",
    "tierna",
    "tierno",
    "amable",
    "agradable",
    "friendly",
    "google",
    "microsoft",
    "online"
];

const TERMINOS_VOZ_TIERNA = [
    "child",
    "kid",
    "boy",
    "girl",
    "junior",
    "young",
    "joven",
    "chico",
    "nino",
    "cute",
    "sweet",
    "happy",
    "angel",
    "soft",
    "suave",
    "friendly"
];

const TERMINOS_VOZ_ROBOTICA = [
    "compact",
    "robot",
    "eloquence",
    "trinoids",
    "whisper",
    "legacy"
];

function obtenerConfigLecturaBot(idioma = obtenerIdiomaActual()) {
    return CONFIG_LECTURA_BOT[idioma] || CONFIG_LECTURA_BOT.es;
}

function lecturaBotSoportada() {
    return (
        typeof window !== "undefined" &&
        "speechSynthesis" in window &&
        typeof SpeechSynthesisUtterance !== "undefined"
    );
}

function cargarVocesLecturaBot() {
    if (!lecturaBotSoportada()) return [];

    vocesLecturaBot = window.speechSynthesis.getVoices() || [];
    return vocesLecturaBot;
}

function inicializarLecturaBot() {
    if (!lecturaBotSoportada()) {
        actualizarBotonesLecturaMensajes();
        return;
    }

    cargarVocesLecturaBot();

    if (typeof window.speechSynthesis.addEventListener === "function") {
        window.speechSynthesis.addEventListener("voiceschanged", () => {
            cargarVocesLecturaBot();
        });
    } else {
        window.speechSynthesis.onvoiceschanged = cargarVocesLecturaBot;
    }

    actualizarBotonesLecturaMensajes();
}

function normalizarCodigoIdioma(codigo = "") {
    return String(codigo).toLowerCase().replace("_", "-");
}

function vozCoincideConIdioma(voz, config) {
    const idiomaVoz = normalizarCodigoIdioma(voz.lang);
    const base = normalizarCodigoIdioma(config.lang).split("-")[0];

    return config.fallbacks.some(fallback => {
        const idiomaFallback = normalizarCodigoIdioma(fallback);
        return (
            idiomaVoz === idiomaFallback ||
            idiomaVoz.startsWith(`${idiomaFallback}-`) ||
            idiomaVoz.split("-")[0] === base
        );
    });
}

function contieneTermino(texto, terminos) {
    return terminos.some(termino => texto.includes(termino));
}

function vozDebeEvitarse(voz, config) {
    const idiomaVoz = normalizarCodigoIdioma(voz.lang);
    const nombreVoz = `${voz.name || ""} ${voz.voiceURI || ""}`.toLowerCase();

    const idiomaEvitado = (config.avoidedLangs || []).some(lang => {
        const langEvitado = normalizarCodigoIdioma(lang);
        return idiomaVoz === langEvitado || idiomaVoz.startsWith(`${langEvitado}-`);
    });

    return idiomaEvitado || contieneTermino(nombreVoz, config.avoidedTerms || []);
}

function puntuarVozLecturaBot(voz, config) {
    const idiomaVoz = normalizarCodigoIdioma(voz.lang);
    const nombreVoz = `${voz.name || ""} ${voz.voiceURI || ""}`.toLowerCase();
    const base = normalizarCodigoIdioma(config.lang).split("-")[0];
    let puntaje = 0;

    config.fallbacks.forEach((fallback, index) => {
        const idiomaFallback = normalizarCodigoIdioma(fallback);

        if (idiomaVoz === idiomaFallback) {
            puntaje += 140 - index * 8;
        } else if (idiomaVoz.startsWith(`${idiomaFallback}-`)) {
            puntaje += 110 - index * 5;
        }
    });

    if (idiomaVoz.split("-")[0] === base) {
        puntaje += 70;
    }

    if (contieneTermino(nombreVoz, config.preferredTerms || [])) {
        puntaje += 34;
    }

    if (contieneTermino(nombreVoz, TERMINOS_VOZ_AMABLE)) {
        puntaje += 24;
    }

    if (contieneTermino(nombreVoz, TERMINOS_VOZ_TIERNA)) {
        puntaje += 22;
    }

    if (contieneTermino(nombreVoz, TERMINOS_VOZ_MASCULINA)) {
        puntaje += 8;
    }

    if (contieneTermino(nombreVoz, TERMINOS_VOZ_ROBOTICA)) {
        puntaje -= 30;
    }

    if (vozDebeEvitarse(voz, config)) {
        puntaje -= 120;
    }

    if (voz.default) {
        puntaje += 2;
    }

    return puntaje;
}

function getPreferredVoice(idioma = obtenerIdiomaActual()) {
    if (!lecturaBotSoportada()) return null;

    const config = obtenerConfigLecturaBot(idioma);
    const voces = vocesLecturaBot.length ? vocesLecturaBot : cargarVocesLecturaBot();
    const vocesDelIdioma = voces.filter(voz => vozCoincideConIdioma(voz, config));
    const vocesSinAcentoEvitado = vocesDelIdioma.filter(voz => !vozDebeEvitarse(voz, config));
    const candidatas = vocesSinAcentoEvitado.length ? vocesSinAcentoEvitado : vocesDelIdioma;

    if (!candidatas.length) return null;

    return candidatas
        .slice()
        .sort((a, b) => puntuarVozLecturaBot(b, config) - puntuarVozLecturaBot(a, config))[0];
}

function limpiarTextoParaLectura(texto) {
    return String(texto || "")
        .replace(/```[\s\S]*?```/g, bloque => bloque.replace(/```[a-z]*\s*/gi, "").replace(/```/g, ""))
        .replace(/`([^`]+)`/g, "$1")
        .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
        .replace(/^\s{0,3}#{1,6}\s*/gm, "")
        .replace(/^\s*[-*+]\s+/gm, "")
        .replace(/[*_~>|]+/g, " ")
        .replace(/\s+/g, " ")
        .trim();
}

function crearIconoLecturaBot() {
    return `
        <svg class="bot-speech-icon bot-speech-icon-sound" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <path d="M4 9v6h4l5 4V5L8 9H4z"></path>
            <path d="M16 8.5a4 4 0 0 1 0 7"></path>
            <path d="M18.5 6a7 7 0 0 1 0 12"></path>
        </svg>
        <svg class="bot-speech-icon bot-speech-icon-stop" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <rect x="7" y="7" width="10" height="10" rx="2"></rect>
        </svg>
    `;
}

function obtenerBotonLecturaDesdeBurbuja(bubble) {
    const stack = bubble ? bubble.closest(".bot-message-stack") : null;
    return stack ? stack.querySelector(".bot-speech-btn") : null;
}

function actualizarEstadoBotonLectura(button, bubble, loading = false) {
    if (!button || !bubble) return;

    const config = obtenerConfigLecturaBot();
    const texto = limpiarTextoParaLectura(bubble.textContent);
    const soportada = lecturaBotSoportada();
    const estaActivo = button === botonLecturaBotActivo;

    button.disabled = !soportada || loading || !texto;
    button.hidden = loading || !texto;
    button.title = soportada ? config.listenLabel : config.unsupportedLabel;
    button.setAttribute("aria-label", estaActivo ? config.stopLabel : config.listenLabel);
    button.classList.toggle("is-speaking", estaActivo);
}

function crearBotonLecturaBot(bubble, loading = false) {
    const button = document.createElement("button");

    button.type = "button";
    button.className = "bot-speech-btn";
    button.innerHTML = crearIconoLecturaBot();

    button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();

        const texto = bubble ? bubble.textContent : "";

        if (
            lecturaBotSoportada() &&
            button === botonLecturaBotActivo &&
            (window.speechSynthesis.speaking || window.speechSynthesis.pending)
        ) {
            stopSpeaking();
            return;
        }

        speakBotMessage(texto, obtenerIdiomaActual(), button);
    });

    actualizarEstadoBotonLectura(button, bubble, loading);

    return button;
}

function actualizarBotonLecturaBurbuja(bubble, loading = false) {
    if (!bubble || !bubble.classList || !bubble.classList.contains("bot")) return null;

    const row = bubble.closest(".message-row.bot-row");

    if (!row) return null;

    let stack = bubble.closest(".bot-message-stack");

    if (!stack) {
        stack = document.createElement("div");
        stack.className = "bot-message-stack";
        row.insertBefore(stack, bubble);
        stack.appendChild(bubble);
    }

    let button = stack.querySelector(".bot-speech-btn");

    if (!button) {
        button = crearBotonLecturaBot(bubble, loading);
        stack.appendChild(button);
    }

    actualizarEstadoBotonLectura(button, bubble, loading);

    return button;
}

function actualizarBotonesLecturaMensajes() {
    document
        .querySelectorAll(".message-row.bot-row .message-bubble.bot")
        .forEach(bubble => actualizarBotonLecturaBurbuja(bubble, bubble.classList.contains("typing")));
}

function resetearBotonLecturaActivo() {
    if (botonLecturaBotActivo) {
        const button = botonLecturaBotActivo;
        const bubble = button.closest(".bot-message-stack")?.querySelector(".message-bubble.bot");

        botonLecturaBotActivo = null;
        button.classList.remove("is-speaking");
        actualizarEstadoBotonLectura(
            button,
            bubble
        );
    }
}

function stopSpeaking() {
    idLecturaBotActual += 1;

    if (lecturaBotSoportada()) {
        window.speechSynthesis.cancel();
    }

    resetearBotonLecturaActivo();
}

function speakBotMessage(texto, idioma = obtenerIdiomaActual(), button = null) {
    if (!lecturaBotSoportada()) {
        console.warn("speechSynthesis no esta disponible en este navegador.");
        return;
    }

    const textoLectura = limpiarTextoParaLectura(texto);

    if (!textoLectura) return;

    if (
        button &&
        button === botonLecturaBotActivo &&
        (window.speechSynthesis.speaking || window.speechSynthesis.pending)
    ) {
        stopSpeaking();
        return;
    }

    window.speechSynthesis.cancel();
    resetearBotonLecturaActivo();

    const config = obtenerConfigLecturaBot(idioma);
    const voz = getPreferredVoice(idioma);
    const utterance = new SpeechSynthesisUtterance(textoLectura);
    const lecturaId = idLecturaBotActual + 1;

    idLecturaBotActual = lecturaId;
    utterance.lang = voz?.lang || config.lang;
    utterance.rate = config.rate || 0.93;
    utterance.pitch = config.pitch || 1.08;
    utterance.volume = 1;

    if (voz) {
        utterance.voice = voz;
    }

    if (button) {
        botonLecturaBotActivo = button;
        actualizarEstadoBotonLectura(
            button,
            button.closest(".bot-message-stack")?.querySelector(".message-bubble.bot")
        );
    }

    utterance.onend = () => {
        if (lecturaId === idLecturaBotActual) {
            resetearBotonLecturaActivo();
        }
    };

    utterance.onerror = () => {
        if (lecturaId === idLecturaBotActual) {
            resetearBotonLecturaActivo();
        }
    };

    window.speechSynthesis.speak(utterance);
}

function setText(id, texto) {const elemento = document.getElementById(id);

if (elemento && texto !== undefined && texto !== null) {
    elemento.textContent = texto;
}

}

function setHTML(id, html) {const elemento = document.getElementById(id);

if (elemento && html !== undefined && html !== null) {
    elemento.innerHTML = html;
}

}

function setPlaceholder(id, texto) {const elemento = document.getElementById(id);

if (elemento && texto !== undefined && texto !== null) {
    elemento.placeholder = texto;
}

}

function aplicarIdiomaDatosCuriosos() {const textos = obtenerTextos();const curiosidades = textos.curiosities || textosIdioma.es.curiosities || [];const tarjetas = document.querySelectorAll(".curiosity-card");

const titulosPanel = {
    es: "Datos curiosos",
    en: "Fun facts",
    pt: "Curiosidades"
};

setText("curiosity-title", titulosPanel[obtenerIdiomaActual()] || titulosPanel.es);

tarjetas.forEach((tarjeta, index) => {
    const curiosidad = curiosidades[index];

    if (!curiosidad) return;

    const titulo = tarjeta.querySelector("h4");
    const descripcion = tarjeta.querySelector("p");

    if (titulo) {
        titulo.textContent = curiosidad.title;
    }

    if (descripcion) {
        descripcion.textContent = curiosidad.text;
    }
});

}

function obtenerQuoteDashboardHTML(texto) {if (!texto) return "";

const palabrasClave = [
    "ayudarte",
    "help you",
    "ajudar você"
];

let resultado = texto;

palabrasClave.forEach(palabra => {
    if (resultado.includes(palabra)) {
        resultado = resultado.replace(palabra, `<span>${palabra}</span>`);
    }
});

return resultado;

}

function obtenerRespuestaBackend(data) {if (!data) return "";

if (typeof data === "string") return data;

return (
    data.respuesta ||
    data.answer ||
    data.response ||
    data.message ||
    data.text ||
    data.result ||
    data.output ||
    data.raw ||
    ""
);

}

function obtenerErrorBackend(data, fallback) {if (!data) return fallback;

if (typeof data === "string") return data || fallback;

if (Array.isArray(data.detail)) {
    return data.detail
        .map(item => item.msg || JSON.stringify(item))
        .join(" | ");
}

return (
    data.detail ||
    data.error ||
    data.message ||
    data.respuesta ||
    data.answer ||
    data.response ||
    data.raw ||
    fallback
);

}

/* ========================================= // CAMBIAR IDIOMA // ========================================= */

function cambiarIdioma() {const selector = document.getElementById("language-select");

if (!selector) return;

localStorage.setItem(LANGUAGE_KEY, selector.value);

stopSpeaking();
aplicarIdioma();
renderizarHistorial();

}

function aplicarIdioma() {const textos = obtenerTextos();const selector = document.getElementById("language-select");

if (selector) {
    selector.value = obtenerIdiomaActual();
}

setText("welcome-title-line-one", textos.welcomeTitleOne);
setText("welcome-title-line-two", textos.welcomeTitleTwo);
setText("welcome-text", textos.welcomeText);
setText("start-btn", textos.startBtn);

setText("sidebar-subtitle", textos.sidebarSubtitle);
setText("sidebar-home", textos.sidebarHome);
setText("sidebar-chat", textos.sidebarChat);
setText("sidebar-settings", textos.sidebarSettings);
setText("sidebar-history", textos.sidebarHistory);
setText("sidebar-support", textos.sidebarSupport);

setText("dashboard-greeting-text", textos.dashboardGreeting);
setText("dashboard-main-name", textos.dashboardName);
setText("dashboard-subtitle", textos.dashboardSubtitle);
setHTML("quote-text", obtenerQuoteDashboardHTML(textos.quoteText));

setText("feature-chat", textos.featureChat);
setText("feature-chat-description", textos.featureChatDescription);
setText("feature-testimonials", textos.featureTestimonials);
setText("feature-testimonials-description", textos.featureTestimonialsDescription);

aplicarIdiomaDatosCuriosos();

setText("news-title", textos.faqTitle);
setText("faq-one-text", textos.faqOne);
setText("faq-two-text", textos.faqTwo);
setText("faq-three-text", textos.faqThree);
setText("faq-four-text", textos.faqFour);
setText("faq-five-text", textos.faqFive);

setText("update-card-one-text", textos.faqOne);
setText("update-card-two-text", textos.faqTwo);
setText("update-card-three-text", textos.faqThree);
setText("update-card-four-text", textos.faqFour);
setText("update-card-five-text", textos.faqFive);

if (typeof aplicarIdiomaFaqAcordeon === "function") {
    aplicarIdiomaFaqAcordeon();
}

setText("notifications-title", textos.notificationsTitle);
setText("notification-one", textos.notificationOne);
setText("notification-two", textos.notificationTwo);

setText("settings-title", textos.settingsTitle);
setText("dark-mode-title", textos.darkModeTitle);
setText("dark-mode-text", textos.darkModeText);
setText("settings-language-title", textos.languageTitle);
setText("settings-language-text", textos.languageText);
setText("accessibility-title", textos.accessibilityTitle);
setText("accessibility-text", textos.accessibilityText);
setText("font-size-title", textos.fontSizeTitle);
setText("font-size-small", textos.fontSmall);
setText("font-size-normal", textos.fontNormal);
setText("font-size-large", textos.fontLarge);
setText("grayscale-title", textos.grayscaleTitle);

setText("history-title", textos.historyTitle);
setPlaceholder("history-search", textos.historySearch);
setText("history-section-title", textos.historySectionTitle);
setText("clear-history-btn", textos.clearHistory);

setText("support-title", textos.supportTitle);
setText("support-subtitle", textos.supportSubtitle);
setText("support-email-text", textos.supportEmailText);
setText("support-phone-text", textos.supportPhoneText);
setText("support-web-text", textos.supportWebText);

setHTML(
    "support-tino-title",
    textos.supportTinoTitle.replace("Tino", "<span>Tino</span>")
);

setText("support-tino-text", textos.supportTinoText);
setText("support-tino-question", textos.supportTinoQuestion);

setText("testimonials-title", textos.testimonialsTitle);
setText("testimonials-subtitle", textos.testimonialsSubtitle);
setText("testimonials-intro-text", textos.testimonialsIntroText);
setText("testimonials-stories-title", textos.testimonialsStoriesTitle);

setText("testimonial-video-one-title", textos.testimonialVideoOneTitle);
setText("testimonial-video-one-text", textos.testimonialVideoOneText);
setText("testimonial-video-one-name", textos.testimonialVideoOneName);

setText("testimonial-video-two-title", textos.testimonialVideoTwoTitle);
setText("testimonial-video-two-text", textos.testimonialVideoTwoText);
setText("testimonial-video-two-name", textos.testimonialVideoTwoName);

setText("testimonial-video-three-title", textos.testimonialVideoThreeTitle);
setText("testimonial-video-three-text", textos.testimonialVideoThreeText);
setText("testimonial-video-three-name", textos.testimonialVideoThreeName);

setText("chat-subtitle", textos.chatSubtitle);
setText("online-status", textos.onlineStatus);
setPlaceholder("msg", textos.inputPlaceholder);

setHTML(
    "voice-title",
    textos.voiceTitle
        .replace("Friend", "<span>Friend</span>")
        .replace("Amigo", "<span>Amigo</span>")
        .replace("amigo", "<span>amigo</span>")
);

setText("voice-subtitle", textos.voiceSubtitle);
setText("voice-instruction", textos.voiceInstruction);
setText("voice-status", textos.voiceReady);
setText("voice-stop-btn", textos.voiceStopButton);
setText("voice-use-text-btn", textos.voiceUseTextButton);

const voiceTranscript = document.getElementById("voice-transcript");

if (
    voiceTranscript &&
    (
        voiceTranscript.textContent.trim() === "" ||
        voiceTranscript.textContent.trim() === textosIdioma.es.voiceTranscriptPlaceholder ||
        voiceTranscript.textContent.trim() === textosIdioma.en.voiceTranscriptPlaceholder ||
        voiceTranscript.textContent.trim() === textosIdioma.pt.voiceTranscriptPlaceholder
    )
) {
    voiceTranscript.textContent = textos.voiceTranscriptPlaceholder;
}

const historial = obtenerHistorial();
const idActual = obtenerConversacionActual();
const conversacion = historial.find(item => item.id === idActual);

if (!conversacion || conversacion.mensajes.length === 0) {
    setText("bot-welcome-message", textos.botWelcome);
}

actualizarBotonesLecturaMensajes();

}

/* ========================================= // HISTORIAL // ========================================= */

function generarIdConversacion() {return "chat_" + Date.now();}

function obtenerHistorial() {try {const data = localStorage.getItem(HISTORY_KEY);return data ? JSON.parse(data) : [];} catch (error) {console.error("Error leyendo historial:", error);return [];}}

function guardarHistorial(historial) {localStorage.setItem(HISTORY_KEY, JSON.stringify(historial));}

function obtenerConversacionActual() {return localStorage.getItem(CURRENT_CHAT_KEY);}

function guardarConversacionActual(id) {localStorage.setItem(CURRENT_CHAT_KEY, id);}

/* ========================================= // LIMPIAR CHAT E HISTORIAL AL RECARGAR // ========================================= */

function paginaFueRecargada() {
    try {
        const navigationEntries =
            typeof performance !== "undefined" &&
            typeof performance.getEntriesByType === "function"
                ? performance.getEntriesByType("navigation")
                : [];

        if (
            navigationEntries &&
            navigationEntries.length > 0 &&
            navigationEntries[0].type === "reload"
        ) {
            return true;
        }

        if (
            typeof performance !== "undefined" &&
            performance.navigation &&
            performance.navigation.type === 1
        ) {
            return true;
        }
    } catch (error) {
        console.error("No se pudo detectar si la página fue recargada:", error);
    }

    return false;
}

function limpiarChatEHistorialAlRecargar() {
    if (!paginaFueRecargada()) return;

    localStorage.removeItem(HISTORY_KEY);
    localStorage.removeItem(CURRENT_CHAT_KEY);

    sessionStorage.removeItem(HISTORY_KEY);
    sessionStorage.removeItem(CURRENT_CHAT_KEY);

    const chat = document.getElementById("chat");

    if (chat) {
        chat.innerHTML = "";
    }

    const input = document.getElementById("msg");

    if (input) {
        input.value = "";
    }

    const historyList = document.getElementById("history-list");

    if (historyList) {
        historyList.innerHTML = "";
    }

    const historySearch = document.getElementById("history-search");

    if (historySearch) {
        historySearch.value = "";
    }

    textoTranscritoFinal = "";

    const transcriptText = document.getElementById("voice-transcript");
    const transcriptBox = document.getElementById("voice-transcript-box");
    const stopBtn = document.getElementById("voice-stop-btn");
    const textos = obtenerTextos();

    if (transcriptText) {
        transcriptText.textContent = textos.voiceTranscriptPlaceholder;
    }

    if (transcriptBox) {
        transcriptBox.classList.add("hidden");
    }

    if (stopBtn) {
        stopBtn.classList.add("hidden");
    }
}

function formatearFechaHora(fechaISO) {const fecha = new Date(fechaISO);const idioma = obtenerIdiomaActual();

const locale =
    idioma === "en" ? "en-US" :
    idioma === "pt" ? "pt-BR" :
    "es-CO";

return fecha.toLocaleString(locale, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
});

}

function crearConversacionSiNoExiste(primerMensaje = "") {let historial = obtenerHistorial();let idActual = obtenerConversacionActual();

let conversacion = historial.find(chat => chat.id === idActual);

if (!conversacion) {
    const textos = obtenerTextos();
    const ahora = new Date().toISOString();

    conversacion = {
        id: generarIdConversacion(),
        titulo: primerMensaje || textos.newConversation,
        createdAt: ahora,
        updatedAt: ahora,
        mensajes: []
    };

    historial.unshift(conversacion);

    guardarHistorial(historial);
    guardarConversacionActual(conversacion.id);
}

return conversacion;

}

function guardarMensajeEnHistorial(tipo, texto) {const ahora = new Date().toISOString();

let historial = obtenerHistorial();
let idActual = obtenerConversacionActual();

let conversacion = historial.find(chat => chat.id === idActual);

if (!conversacion) {
    conversacion = crearConversacionSiNoExiste(texto);
    historial = obtenerHistorial();
}

conversacion = historial.find(chat => chat.id === obtenerConversacionActual());

if (!conversacion) return;

conversacion.mensajes.push({
    tipo,
    texto,
    fecha: ahora
});

if (tipo === "user") {
    const cantidadMensajesUsuario =
        conversacion.mensajes
            .filter(mensaje => mensaje.tipo === "user")
            .length;

    if (cantidadMensajesUsuario === 1) {
        conversacion.titulo =
            texto.length > 45
                ? texto.substring(0, 45) + "..."
                : texto;
    }
}

conversacion.updatedAt = ahora;

historial = historial.filter(chat => chat.id !== conversacion.id);
historial.unshift(conversacion);

guardarHistorial(historial);
renderizarHistorial();

}

function cargarMensajesDeConversacion(idConversacion) {const historial = obtenerHistorial();const conversacion = historial.find(chat => chat.id === idConversacion);

if (!conversacion) return;

guardarConversacionActual(idConversacion);

const chat = document.getElementById("chat");

if (!chat) return;

chat.innerHTML = "";

conversacion.mensajes.forEach(mensaje => {
    agregarMensaje(mensaje.texto, mensaje.tipo, false, false);
});

mostrarChat();

}

function restaurarUltimaConversacion() {const idActual = obtenerConversacionActual();

if (!idActual) return;

const historial = obtenerHistorial();
const conversacion = historial.find(chat => chat.id === idActual);

if (!conversacion || conversacion.mensajes.length === 0) return;

const chat = document.getElementById("chat");

if (!chat) return;

chat.innerHTML = "";

conversacion.mensajes.forEach(mensaje => {
    agregarMensaje(mensaje.texto, mensaje.tipo, false, false);
});

}

function renderizarHistorial(filtro = "") {const historyList = document.getElementById("history-list");

if (!historyList) return;

const textos = obtenerTextos();
const historial = obtenerHistorial();

const historialFiltrado = historial.filter(chat => {
    const textoCompleto = `
        ${chat.titulo}
        ${chat.mensajes.map(mensaje => mensaje.texto).join(" ")}
    `.toLowerCase();

    return textoCompleto.includes(filtro.toLowerCase());
});

if (historialFiltrado.length === 0) {
    historyList.innerHTML = `
        <div class="empty-history">

            <img src="${TINO_IMAGE}"
                 alt="Tino">

            <h3>${textos.emptyHistoryTitle}</h3>

            <p>${textos.emptyHistoryText}</p>

        </div>
    `;

    return;
}

historyList.innerHTML = "";

historialFiltrado.forEach(chat => {
    const ultimoMensaje =
        chat.mensajes.length > 0
            ? chat.mensajes[chat.mensajes.length - 1].texto
            : textos.conversationStarted;

    const preview =
        ultimoMensaje.length > 85
            ? ultimoMensaje.substring(0, 85) + "..."
            : ultimoMensaje;

    const card = document.createElement("button");

    card.classList.add("history-chat-card");

    card.onclick = () => cargarMensajesDeConversacion(chat.id);

    card.innerHTML = `
        <img src="${TINO_IMAGE}"
             alt="Tino"
             class="history-tino-face">

        <div class="history-chat-info">

            <div class="history-chat-top">

                <h3>${chat.titulo}</h3>

                <span>${formatearFechaHora(chat.updatedAt)}</span>

            </div>

            <p>${preview}</p>

        </div>

        <strong class="history-arrow">
            ›
        </strong>
    `;

    historyList.appendChild(card);
});

}

function borrarTodoElHistorial() {const textos = obtenerTextos();

const confirmar = confirm(textos.deleteConfirm);

if (!confirmar) return;

localStorage.removeItem(HISTORY_KEY);
localStorage.removeItem(CURRENT_CHAT_KEY);

renderizarHistorial();
reiniciarChatVisual();

}

function reiniciarChatVisual() {const textos = obtenerTextos();const chat = document.getElementById("chat");

if (!chat) return;

chat.innerHTML = `
    <div class="message-row bot-row">

        <img src="${TINO_IMAGE}"
             alt="Tino"
             class="msg-avatar">

        <div id="bot-welcome-message"
             class="message-bubble bot">

            ${textos.botWelcome}

        </div>

    </div>
`;

actualizarBotonesLecturaMensajes();

}

function iniciarNuevaConversacion() {localStorage.removeItem(CURRENT_CHAT_KEY);reiniciarChatVisual();mostrarChat();}

/* ========================================= // OCULTAR / MOSTRAR PANTALLAS // ========================================= */

const PANTALLAS_CHATBOT = ["chat-welcome","chat-dashboard","chat-real","notificaciones-view","config-view","history-view","support-view","testimonials-view","voice-view"];

function ocultarPantalla(id) {const elemento = document.getElementById(id);

if (!elemento) return null;

elemento.classList.add("hidden");
elemento.style.setProperty("display", "none", "important");

return elemento;

}

function mostrarPantalla(id) {const elemento = document.getElementById(id);

if (!elemento) return null;

elemento.style.removeProperty("display");
elemento.classList.remove("hidden");

return elemento;

}

function ocultarTodasLasPantallas() {PANTALLAS_CHATBOT.forEach(ocultarPantalla);}

/* ========================================= // MENÚ // ========================================= */

function cerrarMenu() {const sidebarMenu = document.getElementById("sidebar-menu");

if (sidebarMenu) {
    sidebarMenu.classList.add("hidden");
    sidebarMenu.style.display = "";
}

}

function abrirMenu() {const chatContainer = document.getElementById("chat-container");const sidebarMenu = document.getElementById("sidebar-menu");

if (!sidebarMenu) {
    console.error("No existe sidebar-menu");
    return;
}

if (chatContainer) {
    chatContainer.classList.remove("hidden");
}

sidebarMenu.classList.remove("hidden");
sidebarMenu.style.display = "flex";

}

/* ========================================= // VISTAS // ========================================= */

function abrirChat() {const chatContainer = document.getElementById("chat-container");const sidebarMenu = document.getElementById("sidebar-menu");

if (!chatContainer) {
    console.error("No existe chat-container");
    return;
}

if (sidebarMenu) {
    sidebarMenu.classList.add("hidden");
}

chatContainer.classList.remove("hidden");

ocultarTodasLasPantallas();

const welcome = mostrarPantalla("chat-welcome");

if (welcome) {
    welcome.classList.remove("hidden");
}

}

function toggleChat() {const chatContainer = document.getElementById("chat-container");const sidebarMenu = document.getElementById("sidebar-menu");

if (!chatContainer) {
    console.error("No existe chat-container");
    return;
}

chatContainer.classList.toggle("hidden");

if (!chatContainer.classList.contains("hidden")) {
    if (sidebarMenu) {
        sidebarMenu.classList.add("hidden");
    }

    ocultarTodasLasPantallas();

    const welcome = mostrarPantalla("chat-welcome");

    if (welcome) {
        welcome.classList.remove("hidden");
    }
} else {
    if (sidebarMenu) {
        sidebarMenu.classList.add("hidden");
    }
}

}

function cerrarChat() {const chatContainer = document.getElementById("chat-container");

detenerGrabacionVoz();

if (chatContainer) {
    chatContainer.classList.add("hidden");
}

cerrarMenu();

}

function mostrarDashboard() {console.log("mostrarDashboard ejecutado desde botón regresar");

detenerGrabacionVoz();

const chatContainer = document.getElementById("chat-container");

if (chatContainer) {
    chatContainer.classList.remove("hidden");
}

ocultarTodasLasPantallas();

const dashboard = mostrarPantalla("chat-dashboard");

if (dashboard) {
    dashboard.classList.remove("hidden");
} else {
    console.error("No existe chat-dashboard");
}

cerrarMenu();

}

function volverDesdeChatAlDashboard() {mostrarDashboard();}

function mostrarChat() {detenerGrabacionVoz();ocultarTodasLasPantallas();

const chatReal = mostrarPantalla("chat-real");
const input = document.getElementById("msg");

if (chatReal) {
    chatReal.classList.remove("hidden");
}

if (input) {
    input.focus();
}

cerrarMenu();

}

function mostrarTestimonios() {detenerGrabacionVoz();ocultarTodasLasPantallas();

const testimonios = mostrarPantalla("testimonials-view");

if (testimonios) {
    testimonios.classList.remove("hidden");
}

cerrarMenu();

}

function mostrarNotificaciones() {detenerGrabacionVoz();ocultarTodasLasPantallas();

const notificaciones = mostrarPantalla("notificaciones-view");

if (notificaciones) {
    notificaciones.classList.remove("hidden");
}

cerrarMenu();

}

function mostrarConfiguracion() {detenerGrabacionVoz();ocultarTodasLasPantallas();

const config = mostrarPantalla("config-view");

if (config) {
    config.classList.remove("hidden");
}

cerrarMenu();

}

function mostrarHistorial() {detenerGrabacionVoz();ocultarTodasLasPantallas();

const historial = mostrarPantalla("history-view");

if (historial) {
    historial.classList.remove("hidden");
}

renderizarHistorial();
cerrarMenu();

}

function mostrarSoporte() {detenerGrabacionVoz();ocultarTodasLasPantallas();

const soporte = mostrarPantalla("support-view");

if (soporte) {
    soporte.classList.remove("hidden");
}

cerrarMenu();

}

/* ========================================= // MODO OSCURO GLOBAL DEL CHATBOT // ========================================= */

function aplicarEstadoModoOscuro(activo) {
    const chatContainer = document.getElementById("chat-container");
    const body = document.body;
    const root = document.documentElement;

    const vistasChatbot = document.querySelectorAll(
        [
            "#chat-container",
            "#chat-welcome",
            "#chat-dashboard",
            "#chat-real",
            "#config-view",
            "#history-view",
            "#support-view",
            "#voice-view",
            "#testimonials-view",
            "#sidebar-menu",
            ".chat-welcome",
            ".dashboard-reference-design",
            ".chat-real",
            ".settings-view",
            ".history-view",
            ".support-view",
            ".voice-view",
            ".testimonials-video-view",
            ".extra-view"
        ].join(",")
    );

    if (chatContainer) {
        chatContainer.classList.toggle("dark-mode", activo);
        chatContainer.setAttribute("data-theme", activo ? "dark" : "light");
    }

    if (body) {
        body.classList.toggle("dark-mode", activo);
        body.classList.toggle("tino-dark-mode", activo);
        body.setAttribute("data-chatbot-theme", activo ? "dark" : "light");
    }

    if (root) {
        root.classList.toggle("dark-mode", activo);
        root.setAttribute("data-chatbot-theme", activo ? "dark" : "light");
    }

    vistasChatbot.forEach((vista) => {
        vista.classList.toggle("dark-mode", activo);
        vista.setAttribute("data-theme", activo ? "dark" : "light");
    });
}

function activarModoOscuro() {
    const toggle = document.getElementById("dark-mode-toggle");

    if (!toggle) {
        console.error("No existe dark-mode-toggle");
        return;
    }

    const activo = toggle.checked;

    aplicarEstadoModoOscuro(activo);
    localStorage.setItem(DARK_MODE_KEY, activo ? "activo" : "inactivo");
}

function cargarModoOscuro() {
    const toggle = document.getElementById("dark-mode-toggle");
    const modoGuardado = localStorage.getItem(DARK_MODE_KEY);
    const activo = modoGuardado === "activo";

    aplicarEstadoModoOscuro(activo);

    if (toggle) {
        toggle.checked = activo;
    }
}



/* Mantiene el modo oscuro aplicado aunque cambies de vista */
function sincronizarModoOscuroDespuesDeCambioDeVista() {
    const activo = localStorage.getItem(DARK_MODE_KEY) === "activo";
    aplicarEstadoModoOscuro(activo);
}

/* ========================================= // ACCESIBILIDAD DEL CHATBOT // ========================================= */

function obtenerElementosConTextoChatbot(chatContainer) {if (!chatContainer) return [];

const candidatos = Array.from(
    chatContainer.querySelectorAll(
        "h1, h2, h3, h4, p, span, strong, small, button, input, select, textarea, label, .message-bubble"
    )
);

return candidatos.filter(elemento => {
    const tag = elemento.tagName ? elemento.tagName.toLowerCase() : "";

    if (["input", "select", "textarea", "button"].includes(tag)) {
        return true;
    }

    return Array.from(elemento.childNodes).some(node =>
        node.nodeType === 3 && node.textContent.trim()
    );
});

}

function limpiarEscalaTipografica(chatContainer) {if (!chatContainer) return;

chatContainer
    .querySelectorAll("[data-tino-font-scaled='true']")
    .forEach(elemento => {
        elemento.style.removeProperty("font-size");
        elemento.style.removeProperty("--tino-base-font-size");
        elemento.removeAttribute("data-tino-font-scaled");
    });

}

function prepararEscalaTipografica(chatContainer) {const elementos = obtenerElementosConTextoChatbot(chatContainer);

const tamanosBase = elementos.map(elemento => ({
    elemento,
    fontSize: window.getComputedStyle(elemento).fontSize
}));

tamanosBase.forEach(({ elemento, fontSize }) => {
    elemento.style.setProperty("--tino-base-font-size", fontSize);
    elemento.style.setProperty(
        "font-size",
        "calc(var(--tino-base-font-size) * var(--chat-font-scale))",
        "important"
    );
    elemento.setAttribute("data-tino-font-scaled", "true");
});

}

function actualizarBotonesTamanoLetra(size) {document.querySelectorAll("[data-font-size]").forEach(boton => {const activo = boton.dataset.fontSize === size;

        boton.classList.toggle("active", activo);
        boton.setAttribute("aria-pressed", activo ? "true" : "false");
    });

}

function aplicarTamanoLetraChatbot(size = "normal") {const tamanosPermitidos = ["small", "normal", "large"];const tamanoSeguro = tamanosPermitidos.includes(size) ? size : "normal";const chatContainer = document.getElementById("chat-container");

if (!chatContainer) return;

aplicandoEscalaTipografica = true;
chatContainer.classList.remove("font-small", "font-normal", "font-large");
limpiarEscalaTipografica(chatContainer);
chatContainer.classList.add(`font-${tamanoSeguro}`);

if (tamanoSeguro !== "normal") {
    prepararEscalaTipografica(chatContainer);
}
aplicandoEscalaTipografica = false;

localStorage.setItem(FONT_SIZE_KEY, tamanoSeguro);
actualizarBotonesTamanoLetra(tamanoSeguro);

}

function aplicarEscalaGrisesChatbot(enabled) {const chatContainer = document.getElementById("chat-container");const toggle = document.getElementById("grayscale-toggle");const activo = Boolean(enabled);

if (!chatContainer) return;

chatContainer.classList.toggle("grayscale-mode", activo);
localStorage.setItem(GRAYSCALE_KEY, activo ? "true" : "false");

if (toggle) {
    toggle.checked = activo;
}

}

function iniciarObservadorAccesibilidad() {const chatContainer = document.getElementById("chat-container");

if (
    !chatContainer ||
    observadorAccesibilidad ||
    typeof MutationObserver === "undefined"
) {
    return;
}

observadorAccesibilidad = new MutationObserver(() => {
    if (aplicandoEscalaTipografica) return;

    const tamanoActual = localStorage.getItem(FONT_SIZE_KEY) || "normal";

    if (tamanoActual !== "normal") {
        const ejecutar =
            typeof requestAnimationFrame === "function"
                ? requestAnimationFrame
                : callback => setTimeout(callback, 0);

        ejecutar(() => {
            aplicarTamanoLetraChatbot(tamanoActual);
        });
    }
});

observadorAccesibilidad.observe(chatContainer, {
    childList: true,
    subtree: true
});

}

function cargarPreferenciasAccesibilidad() {const tamanoGuardado = localStorage.getItem(FONT_SIZE_KEY) || "normal";const escalaGrisesActiva = localStorage.getItem(GRAYSCALE_KEY) === "true";

aplicarTamanoLetraChatbot(tamanoGuardado);
aplicarEscalaGrisesChatbot(escalaGrisesActiva);
iniciarObservadorAccesibilidad();

}

/* ========================================= // RECONOCIMIENTO DE VOZ // ========================================= */

function obtenerReconocimientoVoz() {const SpeechRecognition =window.SpeechRecognition ||window.webkitSpeechRecognition;

const textos = obtenerTextos();

if (!SpeechRecognition) {
    alert(textos.voiceUnsupported);
    return null;
}

const reconocimiento = new SpeechRecognition();
const idiomaActual = obtenerIdiomaActual();

reconocimiento.lang =
    idiomaActual === "en"
        ? "en-US"
        : idiomaActual === "pt"
            ? "pt-BR"
            : "es-CO";

reconocimiento.continuous = true;
reconocimiento.interimResults = true;

return reconocimiento;

}

function abrirVistaVoz() {ocultarTodasLasPantallas();

const voiceView = mostrarPantalla("voice-view");

if (voiceView) {
    voiceView.classList.remove("hidden");
}

cerrarMenu();

textoTranscritoFinal = "";

const textos = obtenerTextos();

const transcriptBox = document.getElementById("voice-transcript-box");
const transcriptText = document.getElementById("voice-transcript");
const stopBtn = document.getElementById("voice-stop-btn");
const status = document.getElementById("voice-status");

if (transcriptBox) {
    transcriptBox.classList.add("hidden");
}

if (transcriptText) {
    transcriptText.textContent = textos.voiceTranscriptPlaceholder;
}

if (stopBtn) {
    stopBtn.classList.add("hidden");
}

if (status) {
    status.textContent = textos.voiceReady;
}

}

function iniciarGrabacionVoz() {detenerGrabacionVoz();

const textos = obtenerTextos();

const status = document.getElementById("voice-status");
const stopBtn = document.getElementById("voice-stop-btn");
const transcriptBox = document.getElementById("voice-transcript-box");
const transcriptText = document.getElementById("voice-transcript");

reconocimientoVoz = obtenerReconocimientoVoz();

if (!reconocimientoVoz) return;

textoTranscritoFinal = "";

if (status) {
    status.textContent = textos.voiceListening;
}

if (stopBtn) {
    stopBtn.classList.remove("hidden");
}

if (transcriptBox) {
    transcriptBox.classList.remove("hidden");
}

if (transcriptText) {
    transcriptText.textContent = textos.voiceListeningText;
}

reconocimientoVoz.onresult = (event) => {
    let textoIntermedio = "";

    for (let i = event.resultIndex; i < event.results.length; i++) {
        const texto = event.results[i][0].transcript;

        if (event.results[i].isFinal) {
            textoTranscritoFinal += texto + " ";
        } else {
            textoIntermedio += texto;
        }
    }

    const resultado = (textoTranscritoFinal + textoIntermedio).trim();

    if (transcriptText) {
        transcriptText.textContent = resultado || textos.voiceListeningText;
    }
};

reconocimientoVoz.onerror = (event) => {
    if (status) {
        status.textContent = textos.voiceError;
    }

    console.error("Error de voz:", event.error);
};

reconocimientoVoz.onend = () => {
    if (stopBtn) {
        stopBtn.classList.add("hidden");
    }

    if (status) {
        status.textContent = textos.voiceStopped;
    }
};

try {
    reconocimientoVoz.start();
} catch (error) {
    console.error("No se pudo iniciar la grabación:", error);
}

}

function detenerGrabacionVoz() {if (reconocimientoVoz) {try {reconocimientoVoz.stop();} catch (error) {console.error("No se pudo detener la grabación:", error);}

    reconocimientoVoz = null;
}

}

function usarTextoTranscrito() {const textos = obtenerTextos();

const transcriptText = document.getElementById("voice-transcript");
const input = document.getElementById("msg");

if (!transcriptText || !input) return;

const texto = transcriptText.textContent.trim();

const textosInvalidos = [
    textos.voiceTranscriptPlaceholder,
    textos.voiceListeningText,
    textos.voiceReady,
    textos.voiceListening,
    textos.voiceStopped,
    textos.voiceError
];

if (texto && !textosInvalidos.includes(texto)) {
    input.value = texto;
}

mostrarChat();
input.focus();

}

/* ========================================= // ENVIAR MENSAJE // ========================================= */

async function enviar() {if (enviando) return;

const input = document.getElementById("msg");
const chat = document.getElementById("chat");
const boton = document.getElementById("send-btn");
const textos = obtenerTextos();

if (!input || !chat) {
    console.error("No existe el input o el chat");
    return;
}

const texto = input.value.trim();
const idiomaActivo = obtenerIdiomaActual();
const idiomaBackend = ["es", "en", "pt"].includes(idiomaActivo)
    ? idiomaActivo
    : "es";

if (!texto) return;

crearConversacionSiNoExiste(texto);

enviando = true;

agregarMensaje(texto, "user", false, true);

input.value = "";
input.focus();

const botBubble = agregarMensaje(
    textos.typing,
    "bot",
    true,
    false
);

try {
    if (boton) {
        boton.disabled = true;
        boton.style.opacity = "0.6";
        boton.style.cursor = "not-allowed";
    }

    const payloadChat = {
        pregunta: texto,
        message: texto,
        language: idiomaBackend,
        query: texto,
        text: texto,
        question: texto,
        input: texto
    };

    if (TINO_DEBUG) {
        console.log("Payload enviado a /chat:", payloadChat);
    }

    const response = await fetch(API_URL, {
        method: "POST",
        mode: "cors",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        body: JSON.stringify(payloadChat)
    });

    let data = null;
    const contentType = response.headers.get("content-type") || "";

    try {
        if (contentType.includes("application/json")) {
            data = await response.json();
        } else {
            const rawText = await response.text();
            data = { raw: rawText };
        }
    } catch (jsonError) {
        data = null;
    }

    if (!response.ok) {
        botBubble.classList.remove("typing");
        botBubble.textContent = obtenerErrorBackend(
            data,
            textos.serverError
        );
        actualizarBotonLecturaBurbuja(botBubble, false);

        guardarMensajeEnHistorial(
            "bot",
            botBubble.textContent
        );

        return;
    }

    botBubble.classList.remove("typing");
    botBubble.textContent =
        obtenerRespuestaBackend(data) || textos.noResponse;
    actualizarBotonLecturaBurbuja(botBubble, false);

    guardarMensajeEnHistorial(
        "bot",
        botBubble.textContent
    );

} catch (error) {
    console.error("Error conectando con backend:", error);

    botBubble.classList.remove("typing");
    botBubble.textContent = textos.connectionError;
    actualizarBotonLecturaBurbuja(botBubble, false);

    guardarMensajeEnHistorial(
        "bot",
        botBubble.textContent
    );

} finally {
    enviando = false;

    if (boton) {
        boton.disabled = false;
        boton.style.opacity = "1";
        boton.style.cursor = "pointer";
    }

    chat.scrollTop = chat.scrollHeight;
}

}

/* ========================================= // AGREGAR MENSAJE // ========================================= */

function agregarMensaje(texto,tipo,loading = false,guardar = false) {const chat = document.getElementById("chat");

if (!chat) {
    console.error("No existe el chat");
    return null;
}

const row = document.createElement("div");

row.classList.add(
    "message-row",
    tipo === "bot" ? "bot-row" : "user-row"
);

const bubble = document.createElement("div");

bubble.classList.add(
    "message-bubble",
    tipo
);

if (loading) {
    bubble.classList.add("typing");
}

bubble.textContent = texto;

if (tipo === "bot") {
    const avatar = document.createElement("img");
    const stack = document.createElement("div");

    avatar.src = TINO_IMAGE;
    avatar.alt = "Tino";
    avatar.classList.add("msg-avatar");
    stack.classList.add("bot-message-stack");

    row.appendChild(avatar);
    stack.appendChild(bubble);
    stack.appendChild(crearBotonLecturaBot(bubble, loading));
    row.appendChild(stack);
} else {
    const icon = document.createElement("div");

    icon.classList.add("user-mini-icon");
    icon.textContent = "👤";

    row.appendChild(bubble);
    row.appendChild(icon);
}

chat.appendChild(row);
chat.scrollTop = chat.scrollHeight;

if (guardar && !loading) {
    guardarMensajeEnHistorial(tipo, texto);
}

return bubble;

}

/* ========================================= // EXPONER FUNCIONES PARA ONCLICK HTML // ========================================= */

window.abrirChat = abrirChat;window.toggleChat = toggleChat;window.cerrarChat = cerrarChat;window.abrirMenu = abrirMenu;window.cerrarMenu = cerrarMenu;window.mostrarDashboard = mostrarDashboard;window.volverDesdeChatAlDashboard = volverDesdeChatAlDashboard;window.mostrarChat = mostrarChat;window.mostrarTestimonios = mostrarTestimonios;window.mostrarNotificaciones = mostrarNotificaciones;window.mostrarConfiguracion = mostrarConfiguracion;window.mostrarHistorial = mostrarHistorial;window.mostrarSoporte = mostrarSoporte;window.enviar = enviar;window.abrirVistaVoz = abrirVistaVoz;window.iniciarGrabacionVoz = iniciarGrabacionVoz;window.detenerGrabacionVoz = detenerGrabacionVoz;window.usarTextoTranscrito = usarTextoTranscrito;window.borrarTodoElHistorial = borrarTodoElHistorial;window.aplicarTamanoLetraChatbot = aplicarTamanoLetraChatbot;window.aplicarEscalaGrisesChatbot = aplicarEscalaGrisesChatbot;window.cargarPreferenciasAccesibilidad = cargarPreferenciasAccesibilidad;window.aplicarIdiomaDatosCuriosos = aplicarIdiomaDatosCuriosos;window.aplicarEstadoModoOscuro = aplicarEstadoModoOscuro;window.limpiarChatEHistorialAlRecargar = limpiarChatEHistorialAlRecargar;window.getPreferredVoice = getPreferredVoice;window.speakBotMessage = speakBotMessage;window.stopSpeaking = stopSpeaking;

/* ========================================= // EVENTOS // ========================================= */

document.addEventListener("DOMContentLoaded", () => {limpiarChatEHistorialAlRecargar();

cargarModoOscuro();

const chatContainerParaModoOscuro = document.getElementById("chat-container");

if (chatContainerParaModoOscuro && typeof MutationObserver !== "undefined") {
    const observadorModoOscuro = new MutationObserver(() => {
        sincronizarModoOscuroDespuesDeCambioDeVista();
    });

    observadorModoOscuro.observe(chatContainerParaModoOscuro, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ["class"]
    });
}


aplicarIdioma();

cargarPreferenciasAccesibilidad();

restaurarUltimaConversacion();

inicializarLecturaBot();

renderizarHistorial();

/* FIX: botones del header del chat real */
const safeBind = (selector, callback) => {
    const element = document.querySelector(selector);

    if (!element) return;

    element.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();

        if (typeof e.stopImmediatePropagation === "function") {
            e.stopImmediatePropagation();
        }

        callback(e);
    }, true);
};

safeBind("#chat-back-dashboard-btn, .real-chat-back-btn", mostrarDashboard);
safeBind("#chat-menu-open-btn, .menu-chat-btn", abrirMenu);
safeBind("#chat-close-btn, .close-chat-btn", cerrarChat);

const input = document.getElementById("msg");

if (input) {
    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            enviar();
        }
    });
}

const darkModeToggle = document.getElementById("dark-mode-toggle");

if (darkModeToggle) {
    darkModeToggle.addEventListener(
        "change",
        activarModoOscuro
    );
}

const languageSelect = document.getElementById("language-select");

if (languageSelect) {
    languageSelect.addEventListener(
        "change",
        cambiarIdioma
    );
}

document
    .querySelectorAll("[data-font-size]")
    .forEach(boton => {
        boton.addEventListener("click", () => {
            aplicarTamanoLetraChatbot(boton.dataset.fontSize);
        });
    });

const grayscaleToggle = document.getElementById("grayscale-toggle");

if (grayscaleToggle) {
    grayscaleToggle.addEventListener("change", () => {
        aplicarEscalaGrisesChatbot(grayscaleToggle.checked);
    });
}

const historySearch = document.getElementById("history-search");

if (historySearch) {
    historySearch.addEventListener("input", (e) => {
        renderizarHistorial(e.target.value);
    });
}

});


/* =========================================================
   TESTIMONIOS: REPRODUCCIÓN Y SCROLL HORIZONTAL
   Un solo bloque: evita listeners duplicados y mantiene usable el iframe.
========================================================= */
(function () {
    function obtenerFilaTestimonios() {
        return (
            document.querySelector("#testimonials-view .testimonial-stories-row") ||
            document.querySelector("#testimonials-view .testimonials-videos-row") ||
            document.querySelector("#testimonials-view .testimonial-videos-row")
        );
    }

    function obtenerTarjetasTestimonios() {
        return Array.from(
            document.querySelectorAll(
                "#testimonials-view .testimonial-story-card, #testimonials-view .testimonial-video-card"
            )
        );
    }

    function detenerOtrosVideos(tarjetaActiva = null) {
        obtenerTarjetasTestimonios().forEach((tarjeta) => {
            if (tarjeta === tarjetaActiva) return;

            const iframe = tarjeta.querySelector("iframe");

            if (iframe && iframe.dataset.originalSrc) {
                iframe.src = iframe.dataset.originalSrc;
            }

            tarjeta.classList.remove("is-playing");
        });
    }

    function prepararIframeYoutube(iframe) {
        if (!iframe) return;

        if (!iframe.dataset.originalSrc) {
            iframe.dataset.originalSrc = iframe.getAttribute("src") || "";
        }

        iframe.setAttribute(
            "allow",
            "autoplay; encrypted-media; picture-in-picture; fullscreen"
        );
        iframe.setAttribute("allowfullscreen", "true");
        iframe.setAttribute("title", iframe.getAttribute("title") || "Video testimonial");
    }

    function activarVideoDesdeTarjeta(tarjeta) {
        if (!tarjeta) return;

        const iframe = tarjeta.querySelector("iframe");

        if (!iframe) return;

        prepararIframeYoutube(iframe);
        detenerOtrosVideos(tarjeta);

        let srcFinal = iframe.dataset.originalSrc || iframe.getAttribute("src") || "";

        try {
            const url = new URL(srcFinal, window.location.origin);

            url.searchParams.set("autoplay", "1");
            url.searchParams.set("playsinline", "1");
            url.searchParams.set("rel", "0");
            url.searchParams.set("modestbranding", "1");
            url.searchParams.set("enablejsapi", "1");

            srcFinal = url.toString();
        } catch (error) {
            const separador = srcFinal.includes("?") ? "&" : "?";
            srcFinal = `${srcFinal}${separador}autoplay=1&playsinline=1&rel=0&modestbranding=1&enablejsapi=1`;
        }

        iframe.src = srcFinal;
        tarjeta.classList.add("is-playing");
    }

    function actualizarPaginacionTestimonios() {
        const fila = obtenerFilaTestimonios();
        const puntos = Array.from(
            document.querySelectorAll("#testimonials-view .testimonials-pagination span")
        );
        const tarjetas = obtenerTarjetasTestimonios();

        if (!fila || !puntos.length || !tarjetas.length) return;

        const centro = fila.scrollLeft + fila.clientWidth / 2;
        let indiceActivo = 0;
        let distanciaMenor = Infinity;

        tarjetas.forEach((tarjeta, index) => {
            const centroTarjeta = tarjeta.offsetLeft + tarjeta.offsetWidth / 2;
            const distancia = Math.abs(centro - centroTarjeta);

            if (distancia < distanciaMenor) {
                distanciaMenor = distancia;
                indiceActivo = index;
            }
        });

        puntos.forEach((punto, index) => {
            punto.classList.toggle(
                "active",
                index === Math.min(indiceActivo, puntos.length - 1)
            );
        });
    }

    function iniciarTestimoniosInteractivos() {
        const vista = document.getElementById("testimonials-view");
        const fila = obtenerFilaTestimonios();

        if (!vista || !fila) return;

        fila.style.overflowX = "auto";
        fila.style.overflowY = "hidden";
        fila.style.scrollSnapType = "x mandatory";
        fila.style.webkitOverflowScrolling = "touch";
        fila.style.touchAction = "pan-x";

        vista.querySelectorAll("iframe").forEach(prepararIframeYoutube);

        vista.querySelectorAll(".testimonial-play-btn").forEach((boton) => {
            if (boton.dataset.bound === "true") return;
            boton.dataset.bound = "true";

            boton.addEventListener("click", (event) => {
                event.preventDefault();
                event.stopPropagation();

                const tarjeta = boton.closest(
                    ".testimonial-story-card, .testimonial-video-card"
                );

                activarVideoDesdeTarjeta(tarjeta);
            });
        });

        if (fila.dataset.boundScroll !== "true") {
            fila.dataset.boundScroll = "true";

            fila.addEventListener(
                "scroll",
                () => window.requestAnimationFrame(actualizarPaginacionTestimonios),
                { passive: true }
            );
        }

        actualizarPaginacionTestimonios();
    }

    document.addEventListener("DOMContentLoaded", iniciarTestimoniosInteractivos);
    window.iniciarTestimoniosInteractivos = iniciarTestimoniosInteractivos;

    const mostrarTestimoniosOriginal = window.mostrarTestimonios;

    window.mostrarTestimonios = function () {
        if (typeof mostrarTestimoniosOriginal === "function") {
            mostrarTestimoniosOriginal.apply(this, arguments);
        }

        setTimeout(iniciarTestimoniosInteractivos, 80);
    };
})();

/* ========================================= // ACORDEÓN PREGUNTAS FRECUENTES - FINAL // ========================================= */

const FAQ_ACORDEON_DATA = {"es": [{"q": "¿Qué es Latinoamérica Comparte?","a": "Latinoamérica Comparte es una organización social que acompaña procesos de emprendimiento, formación, comunidad y transformación humana para emprendedores, familias, líderes y empresas."},{"q": "¿Colombia Comparte y Latinoamérica Comparte son lo mismo?","a": "Colombia Comparte es el contexto histórico de la organización. Actualmente la comunicación se organiza como Latinoamérica Comparte y sus líneas: Comparte Academia, Comparte Liderazgo y Comparte Talento."},{"q": "¿Qué es Comparte Academia?","a": "Comparte Academia es la línea de formación y emprendimiento de Latinoamérica Comparte. Acompaña a personas que quieren emprender, fortalecer una idea o construir un proyecto sostenible."},{"q": "¿Qué es DESCUBRE?","a": "DESCUBRE es un programa inicial para personas que desean emprender, tienen una idea en construcción o necesitan claridad para definir su camino emprendedor."},{"q": "¿Qué es ESTRUCTURA?","a": "ESTRUCTURA es un programa más avanzado para personas que ya tienen una idea de negocio o un emprendimiento en marcha y quieren fortalecerlo de forma estratégica y sostenible."},{"q": "¿Cuánto cuestan los programas?","a": "El programa DESCUBRE cuesta $900.000 COP y el programa ESTRUCTURA cuesta $2.200.000 COP por todo el proceso de formación, mentoría y acompañamiento."},{"q": "¿Puedo entrar si no tengo idea de negocio?","a": "Sí. Puedes ingresar incluso sin una idea completamente definida, porque el programa ayuda a descubrir, estructurar y dar dirección a tus capacidades e intereses."},{"q": "¿Las mentorías son grupales o individuales?","a": "Las mentorías son principalmente grupales. En momentos específicos puede haber acompañamiento personalizado, y la etapa de trabajo de campo incluye mentorías individuales."},{"q": "¿El programa entrega capital semilla?","a": "No se garantiza capital semilla para todos. En algunos casos, si existen recursos o aliados estratégicos, algunos proyectos pueden acceder a oportunidades de apoyo."},{"q": "¿Cómo puedo inscribirme?","a": "Puedes acceder a través de convocatorias, procesos de inscripción, alianzas empresariales o contacto directo con el equipo. Después de inscribirte, el equipo te contacta para orientarte y resolver dudas."}],"en": [{"q": "What is Latinoamérica Comparte?","a": "Latinoamérica Comparte is a social organization that supports entrepreneurship, training, community and human transformation processes for entrepreneurs, families, leaders and companies."},{"q": "Are Colombia Comparte and Latinoamérica Comparte the same?","a": "Colombia Comparte is the historical context of the organization. Today, communication is organized as Latinoamérica Comparte and its lines: Comparte Academia, Comparte Liderazgo and Comparte Talento."},{"q": "What is Comparte Academia?","a": "Comparte Academia is the training and entrepreneurship line of Latinoamérica Comparte. It supports people who want to start a business, strengthen an idea or build a sustainable project."},{"q": "What is DESCUBRE?","a": "DESCUBRE is an initial program for people who want to start a business, have an idea in development or need clarity to define their entrepreneurial path."},{"q": "What is ESTRUCTURA?","a": "ESTRUCTURA is a more advanced program for people who already have a business idea or an active venture and want to strengthen it strategically and sustainably."},{"q": "How much do the programs cost?","a": "The DESCUBRE program costs $900,000 COP and the ESTRUCTURA program costs $2,200,000 COP for the full training, mentoring and support process."},{"q": "Can I join if I do not have a business idea?","a": "Yes. You can join even without a fully defined idea, because the program helps you discover, structure and give direction to your abilities and interests."},{"q": "Are the mentoring sessions group or individual?","a": "Mentoring sessions are mainly group-based. At specific moments there may be personalized support, and the fieldwork stage includes individual mentoring."},{"q": "Does the program provide seed capital?","a": "Seed capital is not guaranteed for everyone. In some cases, if resources or strategic partners are available, some projects may access support opportunities."},{"q": "How can I register?","a": "You can access the program through calls for applications, registration processes, business alliances or direct contact with the team. After registering, the team contacts you to guide you and answer questions."}],"pt": [{"q": "O que é Latinoamérica Comparte?","a": "Latinoamérica Comparte é uma organização social que acompanha processos de empreendedorismo, formação, comunidade e transformação humana para empreendedores, famílias, líderes e empresas."},{"q": "Colombia Comparte e Latinoamérica Comparte são a mesma coisa?","a": "Colombia Comparte é o contexto histórico da organização. Atualmente a comunicação se organiza como Latinoamérica Comparte e suas linhas: Comparte Academia, Comparte Liderazgo e Comparte Talento."},{"q": "O que é Comparte Academia?","a": "Comparte Academia é a linha de formação e empreendedorismo da Latinoamérica Comparte. Acompanha pessoas que querem empreender, fortalecer uma ideia ou construir um projeto sustentável."},{"q": "O que é DESCUBRE?","a": "DESCUBRE é um programa inicial para pessoas que desejam empreender, têm uma ideia em construção ou precisam de clareza para definir seu caminho empreendedor."},{"q": "O que é ESTRUCTURA?","a": "ESTRUCTURA é um programa mais avançado para pessoas que já têm uma ideia de negócio ou um empreendimento em andamento e querem fortalecê-lo de forma estratégica e sustentável."},{"q": "Quanto custam os programas?","a": "O programa DESCUBRE custa $900.000 COP e o programa ESTRUCTURA custa $2.200.000 COP por todo o processo de formação, mentoria e acompanhamento."},{"q": "Posso entrar se não tenho ideia de negócio?","a": "Sim. Você pode entrar mesmo sem uma ideia totalmente definida, porque o programa ajuda a descobrir, estruturar e dar direção às suas capacidades e interesses."},{"q": "As mentorias são em grupo ou individuais?","a": "As mentorias são principalmente em grupo. Em momentos específicos pode haver acompanhamento personalizado, e a etapa de trabalho de campo inclui mentorias individuais."},{"q": "O programa entrega capital semente?","a": "Não há garantia de capital semente para todos. Em alguns casos, se houver recursos ou aliados estratégicos, alguns projetos podem acessar oportunidades de apoio."},{"q": "Como posso me inscrever?","a": "Você pode participar por meio de chamadas, processos de inscrição, alianças empresariais ou contato direto com a equipe. Depois da inscrição, a equipe entra em contato para orientar você e tirar dúvidas."}]};

function obtenerFaqAcordeonActual() {const idioma = obtenerIdiomaActual && typeof obtenerIdiomaActual === "function"? obtenerIdiomaActual(): (localStorage.getItem(LANGUAGE_KEY) || "es");

return FAQ_ACORDEON_DATA[idioma] || FAQ_ACORDEON_DATA.es;

}

function aplicarIdiomaFaqAcordeon() {const preguntas = obtenerFaqAcordeonActual();const items = document.querySelectorAll(".faq-accordion-item");

items.forEach((item, index) => {
    const dato = preguntas[index];

    if (!dato) return;

    const textoPregunta = item.querySelector(".faq-question-text");
    const textoRespuesta = item.querySelector(".faq-answer");
    const boton = item.querySelector(".faq-question");

    if (textoPregunta) {
        textoPregunta.textContent = dato.q;
    }

    if (textoRespuesta) {
        textoRespuesta.textContent = dato.a;
    }

    if (boton) {
        boton.setAttribute("aria-expanded", item.classList.contains("active") ? "true" : "false");
    }
});

}

function inicializarFaqAcordeon() {const preguntas = document.querySelectorAll(".faq-question");

preguntas.forEach((pregunta) => {
    if (pregunta.dataset.faqBound === "true") return;

    pregunta.dataset.faqBound = "true";

    pregunta.addEventListener("click", () => {
        const item = pregunta.closest(".faq-accordion-item");

        if (!item) return;

        const estaAbierto = item.classList.toggle("active");
        pregunta.setAttribute("aria-expanded", estaAbierto ? "true" : "false");
    });
});

aplicarIdiomaFaqAcordeon();

}

document.addEventListener("DOMContentLoaded", () => {inicializarFaqAcordeon();

const selectorIdiomaFaq = document.getElementById("language-select");

if (selectorIdiomaFaq) {
    selectorIdiomaFaq.addEventListener("change", () => {
        setTimeout(aplicarIdiomaFaqAcordeon, 0);
    });
}

});

window.inicializarFaqAcordeon = inicializarFaqAcordeon;window.aplicarIdiomaFaqAcordeon = aplicarIdiomaFaqAcordeon;


/* ========================================= */
/* AJUSTE DEFENSIVO: CHAT COMPACTO */
/* ========================================= */

document.addEventListener("DOMContentLoaded", () => {
    const chatContainer = document.getElementById("chat-container");

    if (chatContainer) {
        chatContainer.classList.add("chat-compact-safe");
    }
});




/* =========================================================
   VOZ: botón "Usar este texto" fuera de la caja
========================================================= */
(function () {
    function sincronizarBotonUsarTextoVoz() {
        const transcriptBox = document.getElementById("voice-transcript-box");
        const useTextBtn = document.getElementById("voice-use-text-btn");

        if (!transcriptBox || !useTextBtn) return;

        const cajaOculta = transcriptBox.classList.contains("hidden");
        useTextBtn.classList.toggle("hidden", cajaOculta);
    }

    document.addEventListener("DOMContentLoaded", () => {
        const transcriptBox = document.getElementById("voice-transcript-box");

        sincronizarBotonUsarTextoVoz();

        if (transcriptBox && typeof MutationObserver !== "undefined") {
            const observer = new MutationObserver(sincronizarBotonUsarTextoVoz);

            observer.observe(transcriptBox, {
                attributes: true,
                attributeFilter: ["class"]
            });
        }
    });

    window.sincronizarBotonUsarTextoVoz = sincronizarBotonUsarTextoVoz;
})();

/* =========================================================
   DATOS CURIOSOS: carrusel automático cada 10 segundos
========================================================= */
(function () {
    const INTERVALO_DATOS_CURIOSOS = 10000;

    function iniciarCarruselDatosCuriosos() {
        const lista = document.querySelector(".curiosity-list");

        if (!lista) return;

        const tarjetas = Array.from(lista.querySelectorAll(".curiosity-card"));

        if (!tarjetas.length) return;

        let indiceActual = tarjetas.findIndex((tarjeta) =>
            tarjeta.classList.contains("active")
        );

        if (indiceActual < 0) {
            indiceActual = 0;
        }

        function mostrarDato(indice) {
            tarjetas.forEach((tarjeta, posicion) => {
                tarjeta.classList.toggle("active", posicion === indice);
            });
        }

        mostrarDato(indiceActual);

        if (window.curiosityAutoTimer) {
            clearInterval(window.curiosityAutoTimer);
        }

        window.curiosityAutoTimer = setInterval(() => {
            indiceActual = (indiceActual + 1) % tarjetas.length;
            mostrarDato(indiceActual);
        }, INTERVALO_DATOS_CURIOSOS);
    }

    document.addEventListener("DOMContentLoaded", iniciarCarruselDatosCuriosos);
    window.iniciarCarruselDatosCuriosos = iniciarCarruselDatosCuriosos;
})();
