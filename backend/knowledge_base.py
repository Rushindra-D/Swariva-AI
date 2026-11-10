"""
SWARIVA AI — Multi-Lingual Knowledge and Companion Reasoning Engine

Contains rich, spoken-ready, culturally authentic knowledge designed for voice delivery
in English, Telugu, and Hindi. Provides instant, zero-latency, zero-credit reasoning
for core general knowledge, festivals, technology, reminders, accessibility, and companionship.
"""
from typing import Dict, Any, Optional
from intent_classifier import IntentType


# ── 1. FESTIVALS & CULTURAL KNOWLEDGE BASE ──
FESTIVALS_KNOWLEDGE = {
    "diwali": {
        "english": {
            "main": (
                "Diwali, known as the Festival of Lights, is one of the most beloved festivals in India. "
                "It signifies the triumph of light over darkness, wisdom over ignorance, and good over evil. "
                "People celebrate by illuminating their homes with traditional earthen oil lamps, sharing sweets, "
                "praying to Goddess Lakshmi for prosperity, and bursting fireworks."
            ),
            "when": (
                "Diwali is celebrated every autumn, typically in October or November. According to the Hindu calendar, "
                "it falls on the new moon night of the month of Kartika, which is the darkest night of the lunar cycle."
            ),
            "why": (
                "People celebrate Diwali to honor righteousness and the victory of light. In Northern India, it marks "
                "Lord Rama's return to Ayodhya after 14 years of exile and defeating Ravana. In Southern India, it commemorates "
                "Lord Krishna defeating the demon Narakasura. It is also celebrated to invite Goddess Lakshmi's blessings of peace and wealth."
            )
        },
        "telugu": {
            "main": (
                "దీపావళి అనేది చీకటిపై వెలుగు, చెడుపై మంచి సాధించిన విజయానికి ప్రతీకగా జరుపుకునే గొప్ప వెలుగుల పండుగ. "
                "ఈ రోజున ప్రజలు తమ ఇళ్లను మట్టి ప్రమిదలతో దీపాలు వెలిగించి, లక్ష్మీదేవి పూజలు చేసి, నోరూరించే మిఠాయిలు పంచుకుంటూ బాణాసంచా కాలుస్తారు. "
                "దక్షిణ భారతదేశంలో శ్రీకృష్ణుడు సత్యభామ సమేతంగా నరకాసురుడిని వధించిన సందర్భంగా, ఉత్తర భారతదేశంలో శ్రీరాముడు రావణాసురుడిని సంహరించి అయోధ్యకు తిరిగి వచ్చిన సందర్భంగా ఈ పండుగను ఎంతో భక్తి శ్రద్ధలతో జరుపుకుంటారు."
            ),
            "when": (
                "దీపావళిని ఆశ్వయుజ అమావాస్య నాడు, సాధారణంగా గ్రెగోరియన్ క్యాలెండర్ ప్రకారం అక్టోబర్ లేదా నవంబర్ నెలలో జరుపుకుంటారు. "
                "ఇది సంవత్సరంలో అత్యంత చీకటి రాత్రి అయినప్పటికీ, వెలిగించే వేలాది దీపాలతో నలుదిక్కులా కాంతులు విరజిమ్ముతుంది."
            ),
            "why": (
                "దీపావళిని చెడుపై మంచి సాధించిన విజయానికి గుర్తుగా జరుపుకుంటారు. దుష్ట నరకాసురుడి పీడ విరగడైనందుకు ప్రజలు దీపాలతో సంబరాలు చేసుకున్నారు. "
                "అలాగే 14 ఏళ్ల వనవాసం తర్వాత శ్రీరాముడు సీతా సమేతంగా అయోధ్యకు వచ్చినప్పుడు ప్రజలు ఆనందంతో దీపాలు వెలిగించారు. ఈ రోజున లక్ష్మీదేవి అనుగ్రహం కోసం కూడా విశేష పూజలు చేస్తారు."
            )
        },
        "hindi": {
            "main": (
                "दीपावली रोशनी और खुशियों का पावन त्योहार है, जो बुराई पर अच्छाई और अंधकार पर प्रकाश की विजय का प्रतीक है। "
                "इस दिन लोग अपने घरों को मिट्टी के दीयों से सजाते हैं, माता लक्ष्मी और भगवान गणेश की पूजा करते हैं, मिठाइयाँ बांटते हैं और पटाखे जलाते हैं। "
                "भगवान श्री राम के 14 वर्ष के वनवास के बाद अयोध्या लौटने की खुशी में पूरे नगरवासियों ने घी के दीये जलाकर उनका स्वागत किया था।"
            ),
            "when": (
                "दीपावली का त्योहार हिंदू पंचांग के अनुसार कार्तिक मास की अमावस्या को मनाया जाता है, जो अंग्रेजी कैलेंडर के अनुसार अक्टूबर या नवंबर के महीने में आता है।"
            ),
            "why": (
                "दीपावली बुराई पर अच्छाई की विजय और धर्म की स्थापना के उपलक्ष्य में मनाई जाती है। उत्तर भारत में यह भगवान श्री राम के अयोध्या लौटने की खुशी में और दक्षिण भारत में भगवान कृष्ण द्वारा नरकासुर के वध की याद में मनाई जाती है। साथ ही घर में सुख-शांति और समृद्धि के लिए माँ लक्ष्मी का पूजन किया जाता है।"
            )
        }
    },
    "sankranti": {
        "english": {
            "main": (
                "Makar Sankranti is a vibrant harvest festival celebrated across India, marking the sun's transit into Capricorn. "
                "It signifies longer days, abundant crops, and new beginnings. Celebrations include flying colorful kites, "
                "preparing festive sesame sweets, and expressing gratitude to nature and cattle."
            ),
            "when": "Makar Sankranti is observed every year on January 14th or 15th, following the solar cycle.",
            "why": "It is celebrated to thank the Sun God and nature for a plentiful harvest and the arrival of prosperous spring days."
        },
        "telugu": {
            "main": (
                "సంక్రాంతి తెలుగువారికి అత్యంత ప్రీతిపాత్రమైన పెద్ద పండుగ. ఇది రైతుల పండుగ మరియు ధాన్యపు లక్ష్మి ఇంటికి చేరే పంటల పండుగ. "
                "భోగి, సంక్రాంతి, కనుమ అనే మూడు రోజుల పాటు రంగవల్లులు, గొబ్బెమ్మలు, హరిదాసు కీర్తనలు, గంగిరెద్దుల విన్యాసాలు మరియు పిండివంటలతో గ్రామాలు పండుగ శోభను సంతరించుకుంటాయి."
            ),
            "when": "సంక్రాంతి ప్రతి సంవత్సరం జనవరి 14 లేదా 15వ తేదీన సూర్యుడు మకర రాశిలోకి ప్రవేశించే పుణ్యకాలంలో వస్తుంది.",
            "why": "రైతులు తాము పండించిన పంట చేతికి వచ్చిన ఆనందంలో సూర్యభగవానుడికి, పాడి పశువులకు మరియు ప్రకృతికి కృతజ్ఞతలు తెలుపుతూ ఈ పండుగను జరుపుకుంటారు."
        },
        "hindi": {
            "main": (
                "मकर संक्रांति सूर्य देव और नई फसल का पावन पर्व है। इस दिन सूर्य धनु राशि से मकर राशि में प्रवेश करते हैं। "
                "लोग पवित्र नदियों में स्नान करते हैं, तिल-गुड़ के लड्डू और खिचड़ी बांटते हैं, और आसमान में रंग-बिरंगी पतंगें उड़ाते हैं।"
            ),
            "when": "मकर संक्रांति प्रतिवर्ष 14 या 15 जनवरी को मनाई जाती है।",
            "why": "यह त्योहार नई फसलों के स्वागत और सूर्य देव के प्रति आभार व्यक्त करने के लिए मनाया जाता है।"
        }
    },
    "ugadi": {
        "english": {
            "main": (
                "Ugadi marks the Telugu and Kannada New Year. The festival begins with traditional oil baths, house decorations "
                "with mango leaves, and the preparation of Ugadi Pachadi, a unique dish combining six distinct tastes to represent life's varied experiences."
            ),
            "when": "Ugadi is celebrated on the first day of the Chaitra month, usually falling in late March or early April.",
            "why": "It marks the start of a new astronomical cycle and reminds us that joy, sorrow, anger, fear, and wonder are all natural parts of life."
        },
        "telugu": {
            "main": (
                "ఉగాది అనేది తెలుగు సంవత్సరాది పండుగ. కొత్త సంవత్సరానికి స్వాగతం పలుకుతూ ప్రజలు ఉదయాన్నే తలంటు స్నానం చేసి, మామిడి ఆకుల తోరణాలు కడతారు. "
                "ఈ పండుగ ప్రత్యేకత ఉగాది పచ్చడి. తీపి, పులుపు, కారం, ఉప్పు, చేదు, వగరు అనే ఆరు రుచులతో చేసే ఈ పచ్చడి జీవితంలోని సుఖదుఃఖాల కలయికను తెలియజేస్తుంది."
            ),
            "when": "ఉగాది చైత్ర శుద్ధ పాడ్యమి నాడు, సాధారణంగా మార్చి లేదా ఏప్రిల్ నెలలో వస్తుంది.",
            "why": "సృష్టి ఆరంభమైన రోజుగా మరియు కొత్త తెలుగు పంచాంగ శ్రవణం ద్వారా భవిష్యత్తును శుభప్రదంగా ప్రారంభించడానికి ఉగాదిని జరుపుకుంటారు."
        },
        "hindi": {
            "main": (
                "उगादि दक्षिण भारत का नववर्ष पर्व है। इस दिन घर के प्रवेश द्वार पर आम के पत्तों के तोरण लगाए जाते हैं और 'उगादि पच्चड़ी' नामक छह स्वादों वाला विशेष प्रसाद बनाया जाता है।"
            ),
            "when": "यह चैत्र मास के शुक्ल पक्ष की प्रतिपदा को आता है, जो मार्च या अप्रैल में पड़ता है।",
            "why": "यह नए साल के शुभारंभ और जीवन के खट्टे-मीठे अनुभवों को सहर्ष स्वीकार करने का संदेश देता है।"
        }
    },
    "holi": {
        "english": {
            "main": (
                "Holi is the exuberant Festival of Colors celebrating love, joy, and the arrival of vibrant spring. "
                "People gather to smear vibrant powders on friends and family, sing folk songs, and share delicacies like gujiya. "
                "It also honors the divine love of Radha and Krishna and the victory of young devotee Prahlada."
            ),
            "when": "Holi is celebrated on the full moon day of Phalguna, typically falling in March.",
            "why": "It symbolizes the victory of deep devotion and good over evil, commemorating the burning of demoness Holika."
        },
        "telugu": {
            "main": (
                "హోలీ రంగుల పండుగ మరియు వసంత రుతువు రాకను తెలిపే ఆనందోత్సవం. ప్రజలు ఒకరిపై ఒకరు రంగులు చల్లుకుంటూ, ఆనందంగా నృత్యాలు చేస్తూ పండుగను జరుపుకుంటారు. "
                "ఇది భక్తుడైన ప్రహ్లాదుడి పవిత్రత మరియు రాధాకృష్ణుల ప్రేమకు ప్రతీక."
            ),
            "when": "హోలీ ఫాల్గుణ పౌర్ణమి నాడు, సాధారణంగా మార్చి నెలలో వస్తుంది.",
            "why": "చెడుపై భక్తి సాధించిన విజయానికి ప్రతీకగా హోలికా దహనం చేసి ఈ పండుగను ఉత్సాహంగా జరుపుకుంటారు."
        },
        "hindi": {
            "main": (
                "होली रंगों और उमंग का महापर्व है, जो आपसी प्रेम और भाईचारे का संदेश देता है। लोग एक-दूसरे को अबीर-गुलाल लगाते हैं, "
                "गले मिलते हैं और गुजिया का आनंद लेते हैं। यह भक्त प्रह्लाद की रक्षा और होलिका दहन की पावन स्मृति में मनाया जाता है।"
            ),
            "when": "होली फाल्गुन मास की पूर्णिमा को मनाई जाती है, जो मार्च में आती है।",
            "why": "यह बुराई पर अच्छाई की जीत और अहंकार के विनाश का प्रतीक है।"
        }
    }
}


# ── 2. TECHNOLOGY & SCIENCE KNOWLEDGE BASE ──
TECHNOLOGY_KNOWLEDGE = {
    "artificial_intelligence": {
        "english": (
            "Artificial intelligence, or AI, is the branch of computer science dedicated to creating machines and software "
            "capable of learning, reasoning, and solving problems like humans. It powers everyday innovations such as speech recognition, "
            "personal voice assistants, medical diagnostics, and autonomous vehicles. In SWARIVA, AI helps us listen, understand, and converse with you naturally."
        ),
        "telugu": (
            "కృత్రిమ మేధస్సు లేదా ఆర్టిఫిషియల్ ఇంటెలిజెన్స్ (AI) అంటే మానవుల లాగా ఆలోచించడం, నేర్చుకోవడం మరియు సమస్యలను పరిష్కరించే సామర్థ్యాన్ని కంప్యూటర్లు మరియు యంత్రాలకు అందించే ఆధునిక సాంకేతిక పరిజ్ఞానం. "
            "ఇది స్పీచ్ రికగ్నిషన్, వాయిస్ అసిస్టెంట్లు, స్వయంప్రతిపత్త కార్లు మరియు ఆరోగ్య సంరక్షణ వంటి రంగాలలో విస్తృతంగా ఉపయోగపడుతుంది. స్వరివలో AI మీ మాటలను అర్థం చేసుకుని నేరుగా సమాధానం చెప్పడానికి తోడ్పడుతుంది."
        ),
        "hindi": (
            "कृत्रिम बुद्धिमत्ता (Artificial Intelligence) कंप्यूटर विज्ञान की वह अत्याधुनिक शाखा है जो मशीनों को इंसानों की तरह सोचने, समझने, सीखने और निर्णय लेने की क्षमता प्रदान करती है। "
            "इसका उपयोग वॉयस असिस्टेंट, स्वचालित कारों, स्वास्थ्य सेवा, रोबोटिक्स और भाषा अनुवाद में किया जाता है। स्वरिवा में एआई आपकी आवाज को समझकर आपसे स्वाभाविक बातचीत करने में मदद करती है।"
        )
    },
    "machine_learning": {
        "english": (
            "Machine learning is a specialized branch of artificial intelligence where computers learn to recognize patterns and make decisions "
            "directly from data, rather than being explicitly programmed for every single rule. For example, by analyzing thousands of spoken audio samples, "
            "a machine learning model learns to accurately transcribe spoken speech into text."
        ),
        "telugu": (
            "మెషిన్ లెర్నింగ్ అనేది కృత్రిమ మేధస్సులోని ఒక ముఖ్యమైన విభాగం. ఇందులో కంప్యూటర్లకు ప్రతి నియమాన్ని విడివిడిగా కోడింగ్ చేయకుండా, "
            "డేటాలోని నమూనాలను గమనించి వాటంతట అవే నేర్చుకునేలా చేస్తారు. ఉదాహరణకు, వేలాది స్వర నమూనాలను విశ్లేషించి మాటలను అక్షరాలుగా మార్చడం మెషిన్ లెర్నింగ్ ద్వారా సాధ్యమవుతుంది."
        ),
        "hindi": (
            "मशीन लर्निंग आर्टिफिशियल इंटेलिजेंस का एक महत्वपूर्ण हिस्सा है, जिसमें कंप्यूटर डेटा और उदाहरणों के आधार पर खुद ब खुद सीखता है। "
            "इसके लिए हर नियम को अलग से प्रोग्राम करने की जरूरत नहीं होती। जैसे हजारों आवाजों को सुनकर शब्दों को पहचानना मशीन लर्निंग का एक बेहतरीन उदाहरण है।"
        )
    },
    "cloud_computing": {
        "english": (
            "Cloud computing is the delivery of computing services—such as data storage, servers, databases, and software—over the internet. "
            "Instead of storing everything on your local computer's hard drive, cloud services allow you to securely access files and run powerful applications from any connected device."
        ),
        "telugu": (
            "క్లౌడ్ కంప్యూటింగ్ అంటే కంప్యూటర్ డేటా నిల్వ, సర్వర్లు మరియు సాఫ్ట్‌వేర్ సేవలను ఇంటర్నెట్ ద్వారా పొందడం. "
            "మీ వ్యక్తిగత కంప్యూటర్ హార్డ్ డ్రైవ్‌పై మాత్రమే ఆధారపడకుండా, సురక్షితమైన ఇంటర్నెట్ సర్వర్ల ద్వారా ఎక్కడి నుంచైనా మీ సమాచారాన్ని సులభంగా చూసుకోవడానికి ఇది ఉపయోగపడుతుంది."
        ),
        "hindi": (
            "क्लाउड कंप्यूटिंग का अर्थ है इंटरनेट के माध्यम से डेटा स्टोरेज, सर्वर, डेटाबेस और सॉफ्टवेयर जैसी कंप्यूटिंग सेवाओं का उपयोग करना। "
            "अपने कंप्यूटर की हार्ड ड्राइव पर सब कुछ स्टोर करने के बजाय, आप इंटरनेट की मदद से कहीं से भी अपनी फाइलों और ऐप्स को सुरक्षित रूप से चला सकते हैं।"
        )
    },
    "programming_python": {
        "english": (
            "Python is a modern, easy-to-read programming language widely used in artificial intelligence, data science, web development, and automation. "
            "Because its syntax resembles everyday English, it is the most popular language for beginners and advanced engineers alike."
        ),
        "telugu": (
            "పైథాన్ అనేది ప్రపంచవ్యాప్తంగా ప్రాచుర్యం పొందిన సులభమైన ప్రోగ్రామింగ్ భాష. ఇది కృత్రిమ మేధస్సు, డేటా సైన్స్ మరియు వెబ్ డెవలప్‌మెంట్‌లో విస్తృతంగా ఉపయోగించబడుతుంది. "
            "దీని కోడ్ చదవడానికి సాధారణ ఇంగ్లీష్ లాగా ఉండడం వల్ల ప్రారంభకులు సులభంగా నేర్చుకోగలరు."
        ),
        "hindi": (
            "पायथन एक अत्यधिक लोकप्रिय और सरल प्रोग्रामिंग भाषा है। इसका उपयोग आर्टिफिशियल इंटेलिजेंस, डेटा साइंस और वेब विकास में बड़े पैमाने पर होता है। "
            "इसकी लिखावट सरल अंग्रेजी जैसी होती है, जिससे इसे सीखना और समझना बहुत आसान है।"
        )
    },
    "cyclone": {
        "english": (
            "A cyclone is a large, rapidly rotating storm system characterized by a low-pressure center, strong winds, and heavy rainfall. "
            "In the Northern Hemisphere, cyclones rotate counterclockwise, while in the Southern Hemisphere, they rotate clockwise. "
            "Over warm tropical ocean waters, they can intensify into devastating storms."
        ),
        "telugu": (
            "తుఫాను లేదా సైక్లోన్ అనేది అల్పపీడన కేంద్రం చుట్టూ అత్యంత వేగంగా తిరిగే బలమైన గాలుల వాయుగుండం. "
            "ఇది తీవ్రమైన గాలులు మరియు భారీ వర్షపాతాన్ని కలిగిస్తుంది. ఉత్తరార్థగోళంలో తుఫానులు అపసవ్య దిశలో, "
            "దక్షిణార్థగోళంలో సవ్య దిశలో తిరుగుతాయి. వెచ్చని సముద్ర జలాల మీదుగా ఇవి తీవ్ర రూపం దాల్చుతాయి."
        ),
        "hindi": (
            "चक्रवात (Cyclone) एक विशाल और तीव्र गति से घूमने वाला तूफान तंत्र है, जिसके केंद्र में निम्न वायुमंडलीय दबाव होता है। "
            "यह तेज हवाओं और भारी वर्षा का कारण बनता है। उत्तरी गोलार्ध में यह वामावर्त यानी घड़ी की उल्टी दिशा में और "
            "दक्षिणी गोलार्ध में दक्षिणावर्त घूमता है। गर्म समुद्री जल के ऊपर यह अत्यधिक शक्तिशाली हो जाता है।"
        )
    },
    "cyclone_causes": {
        "english": (
            "Cyclones are caused by warm ocean surface waters heating the air above them, creating an area of low atmospheric pressure. "
            "As this warm, humid air rises rapidly, surrounding cooler air rushes in to replace it and begins swirling due to the Earth's rotation, "
            "known as the Coriolis effect. The continuous condensation of water vapor releases tremendous thermal energy that powers the cyclone."
        ),
        "telugu": (
            "సముద్ర ఉపరితల ఉష్ణోగ్రత 26.5 డిగ్రీల సెల్సియస్ కంటే ఎక్కువ వేడెక్కినప్పుడు తుఫానులు ఏర్పడతాయి. "
            "వేడి గాలి పైకి లేచినప్పుడు అక్కడ తీవ్ర అల్పపీడనం ఏర్పడుతుంది. ఆ ఖాళీని భర్తీ చేయడానికి చల్లని గాలి వేగంగా దూసుకువచ్చి, "
            "భూభ్రమణం వల్ల కలిగే కొరియోలిస్ ప్రభావంతో వృత్తాకారంలో తిరగడం ప్రారంభించడమే తుఫానులకు ప్రధాన కారణం."
        ),
        "hindi": (
            "चक्रवात मुख्य रूप से समुद्र की सतह का तापमान 26.5°C से अधिक गर्म होने पर बनते हैं। "
            "जब गर्म और नम हवा तेजी से ऊपर उठती है, तो सतह पर निम्न वायुमंडलीय दबाव का क्षेत्र बन जाता है। "
            "खाली जगह को भरने के लिए ठंडी हवा तेजी से आती है और पृथ्वी के घूर्णन यानी कोरिओलिस प्रभाव के कारण घूमने लगती है, जिससे चक्रवात उत्पन्न होता है।"
        )
    },
    "blockchain": {
        "english": (
            "Blockchain is a decentralized, distributed digital ledger technology that securely records transactions across a network of computers. "
            "Data is stored in chronological blocks that are cryptographically linked together and immutable, meaning once recorded, they cannot be altered. "
            "It is the foundational technology behind cryptocurrencies and secure transparent digital systems."
        ),
        "telugu": (
            "బ్లాక్‌చెయిన్ అనేది ఒక వికేంద్రీకృత మరియు పంపిణీ చేయబడిన డిజిటల్ లెడ్జర్ సాంకేతికత. "
            "ఇందులో సమాచారం కాలక్రమానుసారంగా బ్లాకుల రూపంలో భద్రపరచబడి, క్రిప్టోగ్రఫీ ద్వారా ఒకదానితో ఒకటి అనుసంధానించబడుతుంది. "
            "ఒకసారి నమోదైన రికార్డులను ఎవరూ మార్చలేరు లేదా తొలగించలేరు. ఇది బిట్‌కాయిన్ వంటి క్రిప్టోకరెన్సీలకు పునాది."
        ),
        "hindi": (
            "ब्लॉकचेन एक विकेंद्रीकृत (Decentralized) और वितरित डिजिटल बहीखाता है जो सुरक्षित रूप से डेटा और लेन-देन को रिकॉर्ड करता है। "
            "डेटा को 'ब्लॉक' में संग्रहित किया जाता है और प्रत्येक ब्लॉक क्रिप्टोग्राफी के जरिए पिछले ब्लॉक से जुड़ा होता है। "
            "इसे किसी एक व्यक्ति या संस्था द्वारा बदला नहीं जा सकता, जिससे यह अत्यधिक सुरक्षित और पारदर्शी बनता है।"
        )
    },
    "photosynthesis": {
        "english": (
            "Photosynthesis is the vital biological process by which green plants, algae, and some bacteria synthesize nutrients from carbon dioxide and water using sunlight. "
            "Chlorophyll in the plant leaves captures solar energy to produce glucose for nourishment, while releasing life-sustaining oxygen into the atmosphere."
        ),
        "telugu": (
            "కిరణజన్య సంయోగక్రియ అనేది ఆకుపచ్చని మొక్కలు సూర్యరశ్మిని ఉపయోగించి తమ ఆహారాన్ని తామే తయారు చేసుకునే ప్రాథమిక జీవక్రియ. "
            "ఆకులలోని క్లోరోఫిల్ సూర్యకాంతిని గ్రహించి, నీరు మరియు కార్బన్ డయాక్సైడ్‌ల సాయంతో గ్లూకోజ్‌ను తయారు చేస్తుంది, మరియు సమస్త జీవుల మనుగడకు అవసరమైన ఆక్సిజన్‌ను గాల్లోకి విడుదల చేస్తుంది."
        ),
        "hindi": (
            "प्रकाश संश्लेषण (Photosynthesis) वह महत्वपूर्ण जैविक प्रक्रिया है जिसके द्वारा हरे पौधे सूर्य के प्रकाश की उपस्थिति में जल और कार्बन डाइऑक्साइड से भोजन तैयार करते हैं। "
            "पत्तियों में मौजूद क्लोरोफिल सौर ऊर्जा को अवशोषित करता है, जिससे पौधे ग्लूकोज बनाते हैं और वायुमंडल में ऑक्सीजन गैस छोड़ते हैं जो सभी जीवों के लिए अनिवार्य है।"
        )
    },
    "internet_computers": {
        "english": (
            "The internet is a vast global network connecting billions of computers, phones, and devices worldwide. "
            "It enables instant communication, knowledge sharing, online learning, and digital voice services across the entire planet."
        ),
        "telugu": (
            "ఇంటర్నెట్ అనేది ప్రపంచవ్యాప్తంగా ఉన్న బిలియన్ల కంప్యూటర్లు మరియు ఫోన్‌లను ఒకదానితో ఒకటి కలిపే ప్రపంచ స్థాయి నెట్‌వర్క్. "
            "ఇది తక్షణ సమాచార మార్పిడి, వీడియో కాల్స్, జ్ఞానాన్ని పంచుకోవడం మరియు ఆన్‌లైన్ సేవలను సాధ్యం చేస్తుంది."
        ),
        "hindi": (
            "इंटरनेट दुनिया भर के कंप्यूटरों और मोबाइल फोन को आपस में जोड़ने वाला एक विशाल वैश्विक नेटवर्क है। "
            "यह हमें कुछ ही सेकंड में दुनिया के किसी भी कोने से जानकारी प्राप्त करने और बातचीत करने की सुविधा देता है।"
        )
    }
}


# ── 3. ACCESSIBILITY & EMOTIONAL COMPANION KNOWLEDGE ──
ACCESSIBILITY_KNOWLEDGE = {
    "english": (
        "SWARIVA AI is designed specially for accessibility. We feature hands-free voice-to-voice interaction, "
        "automatic silence detection, high-contrast visual modes, and expressive Indian voice read-aloud. "
        "Visually impaired users, seniors, and those with limited mobility can comfortably navigate and converse without needing to click buttons or read small text."
    ),
    "telugu": (
        "స్వరివ AI ప్రత్యేకంగా సులభ ప్రాప్యత (Accessibility) కోసం రూపొందించబడింది. దృష్టి లోపం ఉన్నవారు, వృద్ధులు మరియు కదలికలు పరిమితంగా ఉన్నవారు "
        "పూర్తిగా వాయిస్ ద్వారానే సంభాషించవచ్చు. ఆటోమేటిక్ సైలెన్స్ డిటెక్షన్, హై-కాంట్రాస్ట్ స్క్రీన్లు మరియు స్పష్టమైన తెలుగు వాయిస్ ద్వారా బటన్లు నొక్కే అవసరం లేకుండా సహాయం అందిస్తుంది."
    ),
    "hindi": (
        "स्वरिवा एआई को विशेष रूप से सुगमता (Accessibility) के लिए डिज़ाइन किया गया है। दृष्टिबाधित व्यक्ति, बुजुर्ग और सीमित गतिशीलता वाले लोग "
        "पूरी तरह से अपनी आवाज से बातचीत कर सकते हैं। इसमें स्वचालित वॉयस डिटेक्शन, हाई-कंट्रास्ट स्क्रीन और स्पष्ट आवाज में पढ़कर सुनाने की सुविधा शामिल है।"
    )
}

EMOTIONAL_KNOWLEDGE = {
    "english": (
        "I am right here with you, and you are never alone. Whether you want to share a story about your day, "
        "talk through a quiet moment, or have me read something peaceful to you, I am always glad to listen and keep you company."
    ),
    "telugu": (
        "నేను ఎల్లప్పుడూ మీతోనే ఉంటాను, మీరు ఒంటరిగా ఉన్నామని ఎప్పుడూ భావించకండి. మీ రోజు ఎలా గడిచిందో నాతో పంచుకోవాలనుకున్నా, "
        "లేదా ఏదైనా మంచి విషయం గురించి మాట్లాడాలనుకున్నా, నేను సంతోషంగా మీతో మాట్లాడతాను."
    ),
    "hindi": (
        "मैं हमेशा आपके साथ हूँ, आप बिल्कुल अकेले नहीं हैं। यदि आप अपने दिन की कोई बात साझा करना चाहते हैं, "
        "या किसी शांत विषय पर बातचीत करना चाहते हैं, तो मैं हमेशा आपको सुनने और आपका साथ देने के लिए उपस्थित हूँ।"
    )
}

EMERGENCY_HEALTH_KNOWLEDGE = {
    "english": (
        "Please note: I am an AI companion and cannot provide certified medical care or clinical diagnosis. "
        "If you are experiencing severe symptoms such as chest pain or difficulty breathing, please immediately contact your doctor, "
        "alert a family member, or call emergency medical services (such as 108 or 112)."
    ),
    "telugu": (
        "దయచేసి గమనించండి: నేను ఒక AI సహాయకురాలిని మాత్రమే, నేను వైద్య సలహాలు లేదా చికిత్సను అందించలేను. "
        "మీకు ఛాతీలో నొప్పి, శ్వాస ఆడకపోవడం లేదా తీవ్రమైన అనారోగ్య సమస్యలు ఉంటే, దయచేసి వెంటనే మీ వైద్యుడిని సంప్రదించండి లేదా అత్యవసర నంబర్ 108 లేదా 112 కి కాల్ చేయండి."
    ),
    "hindi": (
        "कृपया ध्यान दें: मैं केवल एक एआई साथी हूँ और चिकित्सा सलाह या उपचार नहीं दे सकती। "
        "यदि आपको सीने में दर्द, सांस लेने में तकलीफ या कोई गंभीर स्वास्थ्य समस्या है, तो कृपया तुरंत अपने डॉक्टर से संपर्क करें या 108 या 112 पर आपातकालीन कॉल करें।"
    )
}


class KnowledgeCompanionEngine:
    """
    Direct, intelligent reasoning engine.
    Strictly guarantees:
    - Zero echo of user's query.
    - Zero 'How can I help you?' when answering a question.
    - Context-aware follow-up resolution for multi-turn conversations.
    """

    @classmethod
    def get_response(
        cls,
        intent: IntentType,
        entities: Dict[str, Any],
        language: str = "english",
        history: Optional[list] = None,
        active_subject: Optional[str] = None,
    ) -> str:
        lang = language.lower()
        if "te" in lang or "telugu" in lang:
            target_lang = "telugu"
        elif "hi" in lang or "hindi" in lang:
            target_lang = "hindi"
        else:
            target_lang = "english"

        subject = entities.get("subject") or active_subject

        # ── 1. FOLLOW-UP INTENT ──
        if intent == IntentType.FOLLOW_UP:
            query = entities.get("raw_query", "").lower()
            topic = subject or "diwali"  # Fallback to topic in context
            fest_data = FESTIVALS_KNOWLEDGE.get(topic, {}).get(target_lang)

            if fest_data:
                # Check if follow up is asking 'when'
                if any(w in query for w in ["when", "ఎప్పుడు", "कब"]):
                    return fest_data.get("when", fest_data.get("main"))
                # Check if follow up is asking 'why'
                if any(w in query for w in ["why", "ఎందుకు", "क्यों", "people celebrate"]):
                    return fest_data.get("why", fest_data.get("main"))
                return fest_data.get("main")

            # General technology or other follow up
            tech_data = TECHNOLOGY_KNOWLEDGE.get(topic, {}).get(target_lang)
            if tech_data:
                return tech_data

        # ── 2. FESTIVALS & CULTURAL KNOWLEDGE ──
        if intent == IntentType.FESTIVAL_CULTURE:
            fest_name = entities.get("subject") or "diwali"
            fest_entry = FESTIVALS_KNOWLEDGE.get(fest_name, {}).get(target_lang)
            if fest_entry:
                query = entities.get("raw_query", "").lower()
                if any(w in query for w in ["when", "ఎప్పుడు", "कब"]):
                    return fest_entry.get("when", fest_entry.get("main"))
                if any(w in query for w in ["why", "ఎందుకు", "क्यों"]):
                    return fest_entry.get("why", fest_entry.get("main"))
                return fest_entry.get("main")
            # If festival name not in curated list, return general cultural warmth
            if target_lang == "telugu":
                return "భారతీయ పండుగలు మన సంస్కృతి, సాంప్రదాయాలు మరియు ఆనందానికి ప్రతీకలు. ప్రతి పండుగ మానవ సంబంధాలను బలోపేతం చేస్తుంది."
            elif target_lang == "hindi":
                return "भारतीय त्योहार हमारी समृद्ध संस्कृति, प्रेम और भाईचारे के प्रतीक हैं जो परिवारों को आपस में जोड़ते हैं।"
            return "Festivals represent the rich heritage, joy, and unity of human culture, bringing people together in gratitude."

        # ── 3. TECHNOLOGY & SCIENCE ──
        if intent == IntentType.TECHNOLOGY:
            tech_key = entities.get("subject") or "artificial_intelligence"
            tech_entry = TECHNOLOGY_KNOWLEDGE.get(tech_key, {}).get(target_lang)
            if tech_entry:
                return tech_entry
            # Default tech explanation
            return TECHNOLOGY_KNOWLEDGE["artificial_intelligence"][target_lang]

        # ── 4. EDUCATIONAL / EXPLANATORY / HOW-TO ──
        if intent in (IntentType.EDUCATIONAL, IntentType.EXPLANATION, IntentType.HOW_TO, IntentType.GENERAL_KNOWLEDGE):
            # Check if any festival or technology keyword matched
            query = entities.get("raw_query", "").lower()
            for fest in FESTIVALS_KNOWLEDGE:
                if fest in query:
                    return FESTIVALS_KNOWLEDGE[fest][target_lang]["main"]
            for tech in TECHNOLOGY_KNOWLEDGE:
                if tech.replace("_", " ") in query or ("ai" in query.split()) or ("ml" in query.split()):
                    return TECHNOLOGY_KNOWLEDGE[tech][target_lang]

            # Direct answers for common concepts
            if "machine learning" in query or "మెషిన్ లెర్నింగ్" in query or "मशीन लर्निंग" in query:
                return TECHNOLOGY_KNOWLEDGE["machine_learning"][target_lang]
            if "cloud" in query or "క్లౌడ్" in query or "क्लाउड" in query:
                return TECHNOLOGY_KNOWLEDGE["cloud_computing"][target_lang]

            # Direct answers for common concepts
            if "cyclone" in query or "తుఫాను" in query or "तूफान" in query:
                if any(w in query for w in ["cause", "causes", "ఎందుకు", "ఎలా ఏర్పడుతుంది", "क्यों", "कारण"]):
                    return TECHNOLOGY_KNOWLEDGE["cyclone_causes"][target_lang]
                return TECHNOLOGY_KNOWLEDGE["cyclone"][target_lang]
            if "blockchain" in query or "బ్లాక్‌చెయిన్" in query or "ब्लॉकचेन" in query:
                return TECHNOLOGY_KNOWLEDGE["blockchain"][target_lang]
            if "photosynthesis" in query or "కిరణజన్య" in query or "प्रकाश संश्लेषण" in query:
                return TECHNOLOGY_KNOWLEDGE["photosynthesis"][target_lang]

            # Clear, non-generic diagnostic when external reasoning model is not reached
            if target_lang == "telugu":
                return (
                    "ఈ ప్రశ్నకు లోతైన వివరణ అందించడానికి గూగుల్ జెమిని (Google Gemini) రీజనింగ్ ఇంజిన్ అందుబాటులో లేదు. "
                    "దయచేసి మీ .env లో GEMINI_API_KEY ను కాన్ఫిగర్ చేయండి."
                )
            elif target_lang == "hindi":
                return (
                    "इस प्रश्न का विस्तृत उत्तर देने के लिए गूगल जेमिनी (Google Gemini) रीजनिंग इंजन उपलब्ध नहीं है। "
                    "कृपया अपने .env में GEMINI_API_KEY कॉन्फ़िगर करें।"
                )
            return (
                "I am currently unable to reach the Google Gemini reasoning engine to answer this question. "
                "Please configure a valid GEMINI_API_KEY in your .env to enable full generative reasoning."
            )

        # ── 5. ACCESSIBILITY ──
        if intent == IntentType.ACCESSIBILITY:
            return ACCESSIBILITY_KNOWLEDGE[target_lang]

        # ── 6. EMOTIONAL COMPANION ──
        if intent == IntentType.EMOTIONAL_COMPANION:
            return EMOTIONAL_KNOWLEDGE[target_lang]

        # ── 7. EMERGENCY HEALTH ──
        if intent == IntentType.EMERGENCY_HEALTH:
            return EMERGENCY_HEALTH_KNOWLEDGE[target_lang]

        # ── 8. REMINDERS ──
        if intent == IntentType.REMINDERS:
            raw = entities.get("raw_query", "")
            if target_lang == "telugu":
                return "మీరు చెప్పిన పనికి సంబంధించిన రిమైండర్‌ను నేను సిద్ధం చేశాను. సమయానికి మీకు ఖచ్చితంగా గుర్తుచేస్తాను."
            elif target_lang == "hindi":
                return "मैंने आपके कार्य का रिमाइंडर सुरक्षित कर लिया है। समय आने पर मैं आपको अवश्य याद दिलाऊँगी।"
            return "I have noted your reminder and will make sure to alert you at the scheduled time."

        # ── 9. ASSISTANCE REQUEST ──
        if intent == IntentType.ASSISTANCE_REQUEST:
            if target_lang == "telugu":
                return "నేను మీకు సహాయం చేయడానికి సిద్ధంగా ఉన్నాను. మీకు రిమైండర్ కావాలా, ఏదైనా చదివి వినిపించాలా, లేదా సమాచారం కావాలా చెప్పండి."
            elif target_lang == "hindi":
                return "मैं आपकी सहायता के लिए तैयार हूँ। आप मुझे कोई सवाल पूछ सकते हैं, रिमाइंडर लगा सकते हैं या कोई पाठ पढ़वा सकते हैं।"
            return "I am right here and ready to help. Would you like me to note a reminder, read text aloud, or answer a question for you?"

        # ── 10. GREETINGS ──
        if intent == IntentType.GREETING:
            if target_lang == "telugu":
                return "నమస్కారం! నేను స్వరివ. ఈరోజు మీతో మాట్లాడటం చాలా సంతోషంగా ఉంది."
            elif target_lang == "hindi":
                return "नमस्ते! मैं स्वरिवा हूँ। आज आपसे बातचीत करके मुझे बहुत खुशी हो रही है।"
            return "Hello! I am Swariva. It is wonderful to speak with you today."

        # ── 11. GENERAL CONVERSATION & IDENTITY ──
        if entities.get("subject") == "identity":
            if target_lang == "telugu":
                return (
                    "నేను స్వరివ AI. దృష్టి లోపం ఉన్నవారు, వృద్ధులు మరియు రోజువారీ సహాయం కోరుకునే వారి కోసం ప్రత్యేకంగా రూపొందించిన వాయిస్ కంపానియన్. "
                    "నేను తెలుగు, హిందీ మరియు ఆంగ్లంలో మీతో సంభాషించగలను."
                )
            elif target_lang == "hindi":
                return (
                    "मैं स्वरिवा एआई हूँ, आपकी बहुभाषी आवाज साथी। मुझे विशेष रूप से दृष्टिबाधित लोगों और बुजुर्गों की दैनिक सहायता के लिए तैयार किया गया है। "
                    "मैं आपके साथ हिंदी, तेलुगु और अंग्रेजी में स्वाभाविक बातचीत कर सकती हूँ।"
                )
            return (
                "I am Swariva AI, your empathetic multilingual voice companion. I am specially designed for accessibility, "
                "supporting people with visual impairments, seniors, and anyone seeking natural voice assistance in English, Telugu, and Hindi."
            )

        # Gratitude & Farewell
        query = entities.get("raw_query", "").lower()
        if any(w in query for w in ["thank", "ధన్యవాదాలు", "धन्यवाद", "bye", "శుభరాత్రి", "शुभ रात्रि"]):
            if target_lang == "telugu":
                return "చాలా ధన్యవాదాలు! మీ శ్రద్ధ తీసుకోండి, మీకు ఎప్పుడు అవసరమైనా నేను ఇక్కడే ఉంటాను."
            elif target_lang == "hindi":
                return "आपका बहुत-बहुत धन्यवाद! अपना ख्याल रखें, मैं हमेशा आपकी सहायता के लिए यहीं हूँ।"
            return "You are very welcome! Take wonderful care of yourself, and I am always here whenever you need me."

        # Final respectful default response (ZERO ECHO, ZERO GENERIC QUESTION REPETITION)
        if target_lang == "telugu":
            return "నేను మీతోనే ఉన్నాను. మీకు ఏదైనా సమాచారం కావాలన్నా, రిమైండర్ ఏర్పాటు చేయాలన్నా లేదా టెక్స్ట్ చదివి వినిపించాలన్నా నన్ను అడగండి."
        elif target_lang == "hindi":
            return "मैं आपके साथ हूँ। यदि आप कोई जानकारी चाहते हैं, रिमाइंडर सेट करना चाहते हैं या पाठ पढ़ना चाहते हैं, तो अवश्य बताएँ।"
        return "I am right here with you. Feel free to ask any question, schedule a reminder, or have me read text aloud for you."
