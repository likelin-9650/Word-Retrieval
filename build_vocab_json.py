import json

entries = []

def add(word, pos, irregulars=None, variants=None):
    entries.append({
        "word": word,
        "pos": pos if isinstance(pos, list) else [pos],
        "irregulars": irregulars or [],
        "variants": variants or []
    })

# Page 1
add("a", ["art"], variants=["an"])
for w, p in [
    ("abandon", ["v"]), ("ability", ["n"]), ("able", ["a"]), ("abnormal", ["a"]),
    ("aboard", ["prep"]), ("abolish", ["v"]), ("abortion", ["n"]), ("about", ["ad", "prep"]),
    ("above", ["prep", "a", "ad"]), ("abroad", ["ad"]), ("abrupt", ["a"]), ("absence", ["n"]),
    ("absent", ["a"]), ("absolute", ["a"]), ("absorb", ["v"]), ("abstract", ["a", "n"]),
    ("absurd", ["a"]), ("abundant", ["a"]), ("abuse", ["v"]), ("academic", ["a", "n"]),
    ("academy", ["n"]), ("accelerate", ["v"]), ("accent", ["n"]), ("accept", ["v"]),
    ("access", ["n", "v"]), ("accessible", ["a"]), ("accident", ["n"]),
    ("accommodation", ["n"]), ("accompany", ["v"]), ("accomplish", ["v"]), ("account", ["n"]),
    ("accountant", ["n"]), ("accumulate", ["v"]), ("accuracy", ["n"]), ("accurate", ["a"]),
    ("accuse", ["v"]), ("accustomed", ["a"]), ("ache", ["v", "n"]), ("achieve", ["v"]),
    ("achievement", ["n"]), ("acid", ["a"]), ("acknowledge", ["v"]), ("acquaintance", ["n"]),
    ("acquire", ["v"]), ("acquisition", ["n"]), ("acre", ["n"]), ("across", ["prep"]),
    ("act", ["n", "v"]), ("action", ["n"]), ("active", ["a"]), ("activity", ["n"]),
    ("actor", ["n"]), ("actress", ["n"]), ("actual", ["a"]), ("acute", ["a"]), ("AD", ["abbr"]),
]:
    add(w, p)

# Page 2
add("ad", ["n"], variants=["advertisement"])
for w, p in [
    ("adapt", ["v"]), ("adaptation", ["n"]), ("add", ["v"]), ("addicted", ["a"]),
    ("addition", ["n"]), ("address", ["n"]), ("adequate", ["a"]), ("adjust", ["v"]),
    ("adjustment", ["n"]), ("administration", ["n"]), ("admirable", ["a"]), ("admire", ["v"]),
    ("admission", ["n"]), ("admit", ["v"]), ("adolescence", ["n"]), ("adolescent", ["a", "n"]),
    ("adopt", ["v"]), ("adore", ["v"]), ("adult", ["n"]), ("advance", ["v", "n"]),
    ("advantage", ["n"]), ("adventure", ["n"]), ("advertise", ["v"]), ("advertisement", ["n"]),
    ("advice", ["n"]), ("advise", ["v"]), ("advocate", ["v"]), ("affair", ["n"]),
    ("affect", ["v"]), ("affection", ["n"]), ("afford", ["v"]), ("afraid", ["a"]),
    ("Africa", ["n"]), ("African", ["a", "n"]), ("after", ["ad", "prep", "conj"]),
    ("afternoon", ["n"]), ("again", ["ad"]), ("against", ["prep"]), ("age", ["n"]),
    ("agency", ["n"]), ("agenda", ["n"]), ("agent", ["n"]), ("aggressive", ["a"]),
    ("ago", ["ad"]), ("agree", ["v"]), ("agreement", ["n"]), ("agricultural", ["a"]),
    ("agriculture", ["n"]), ("ahead", ["ad"]), ("aid", ["n", "v"]), ("AIDS", ["n"]),
    ("aim", ["n", "v"]), ("air", ["n"]), ("aircraft", ["n"]), ("airline", ["n"]),
    ("airmail", ["n"]), ("airplane", ["n"]), ("airport", ["n"]), ("airspace", ["n"]),
    ("alarm", ["n", "v"]),
]:
    add(w, p)
add("afterward", ["ad"], variants=["afterwards"])

# Page 3
for w, p in [
    ("album", ["n"]), ("alcohol", ["n"]), ("alcoholic", ["a", "n"]), ("algebra", ["n"]),
    ("alike", ["ad"]), ("alive", ["a"]), ("all", ["ad", "a", "pron"]), ("allergic", ["a"]),
    ("alley", ["n"]), ("allocate", ["v"]), ("allow", ["v"]), ("allowance", ["n"]),
    ("almost", ["ad"]), ("alone", ["a"]), ("along", ["ad", "prep"]), ("alongside", ["ad"]),
    ("aloud", ["ad"]), ("alphabet", ["n"]), ("already", ["ad"]), ("also", ["ad"]),
    ("alternative", ["a"]), ("although", ["conj"]), ("altitude", ["n"]), ("altogether", ["ad"]),
    ("always", ["ad"]), ("am", ["v"]), ("amateur", ["a"]), ("amaze", ["v"]),
    ("amazing", ["a"]), ("ambassador", ["n"]), ("ambassadress", ["n"]), ("ambiguous", ["a"]),
    ("ambition", ["n"]), ("ambulance", ["n"]), ("America", ["n"]), ("among", ["prep"]),
    ("amount", ["n", "v"]), ("ample", ["a"]), ("amuse", ["v"]), ("amusement", ["n"]),
    ("analyse", ["v"]), ("analysis", ["n"]), ("ancestor", ["n"]), ("anchor", ["v", "n"]),
    ("ancient", ["a"]), ("and", ["conj"]), ("anecdote", ["n"]), ("anger", ["n"]),
    ("angle", ["n"]), ("angry", ["a"]), ("animal", ["n"]), ("ankle", ["n"]),
    ("anniversary", ["n"]), ("announce", ["v"]), ("annoy", ["v"]), ("annual", ["a"]),
    ("another", ["a", "pron"]), ("answer", ["n", "v"]), ("ant", ["n"]),
]:
    add(w, p)
add("aluminium", ["n"], variants=["aluminum"])
add("a.m.", ["abbr"], variants=["am", "A.M.", "AM"])

# Page 4
for w, p in [
    ("Antarctic", ["a"]), ("antique", ["n"]), ("anxiety", ["n"]), ("anxious", ["a"]),
    ("any", ["pron", "a"]), ("anybody", ["pron"]), ("anyhow", ["ad"]), ("anyone", ["pron"]),
    ("anything", ["pron"]), ("anyway", ["ad"]), ("anywhere", ["ad"]), ("apart", ["ad", "a"]),
    ("apartment", ["n"]), ("apologize", ["v"]), ("apology", ["n"]), ("apparent", ["a"]),
    ("appeal", ["v", "n"]), ("appear", ["v"]), ("appearance", ["n"]), ("appendix", ["n"]),
    ("appetite", ["n"]), ("applaud", ["v", "n"]), ("apple", ["n"]), ("applicant", ["n"]),
    ("application", ["n"]), ("apply", ["v"]), ("appoint", ["v"]), ("appointment", ["n"]),
    ("appreciate", ["v"]), ("appreciation", ["n"]), ("approach", ["n", "v"]),
    ("appropriate", ["a"]), ("approval", ["n"]), ("approve", ["v"]), ("approximately", ["ad"]),
    ("apron", ["n"]), ("arbitrary", ["a"]), ("arch", ["n"]), ("architect", ["n"]),
    ("architecture", ["n"]), ("Arctic", ["a"]), ("are", ["v"]), ("area", ["n"]),
    ("argue", ["v"]), ("argument", ["n"]), ("arithmetic", ["n"]), ("arm", ["n", "v"]),
    ("armchair", ["n"]), ("army", ["n"]), ("around", ["ad", "prep"]), ("arrange", ["v"]),
    ("arrangement", ["n"]), ("arrest", ["v"]), ("arrival", ["n"]), ("arrive", ["v"]),
    ("arrow", ["n"]), ("art", ["n"]), ("article", ["n"]), ("artificial", ["a"]),
    ("artist", ["n"]), ("as", ["ad", "conj", "prep"]),
]:
    add(w, p)
add("arise", ["v"], irregulars=["arose", "arisen"])

# Page 5
for w, p in [
    ("ash", ["n"]), ("ashamed", ["a"]), ("Asia", ["n"]), ("Asian", ["a", "n"]),
    ("aside", ["ad"]), ("ask", ["v"]), ("asleep", ["a"]), ("aspect", ["n"]),
    ("assess", ["v"]), ("assessment", ["n"]), ("assist", ["v"]), ("assistance", ["n"]),
    ("assistant", ["n"]), ("associate", ["v"]), ("association", ["n"]), ("assume", ["v"]),
    ("assumption", ["n"]), ("astonish", ["v"]), ("astronaut", ["n"]), ("astronomer", ["n"]),
    ("astronomy", ["n"]), ("at", ["prep"]), ("athlete", ["n"]), ("athletic", ["a"]),
    ("Atlantic", ["a"]), ("atmosphere", ["n"]), ("atom", ["n"]), ("attach", ["v"]),
    ("attack", ["v", "n"]), ("attain", ["v"]), ("attempt", ["v", "n"]), ("attend", ["v"]),
    ("attention", ["n"]), ("attitude", ["n"]), ("attract", ["v"]), ("attraction", ["n"]),
    ("attractive", ["a"]), ("audience", ["n"]), ("aunt", ["n"]), ("authentic", ["a"]),
    ("author", ["n"]), ("authority", ["n"]), ("automatic", ["a"]), ("autonomous", ["a"]),
    ("autumn", ["n"]), ("available", ["a"]), ("avenue", ["n"]), ("average", ["a", "n"]),
    ("avoid", ["v"]), ("award", ["n"]), ("aware", ["a"]), ("away", ["ad"]),
    ("awesome", ["a"]), ("awful", ["a"]), ("awkward", ["a"]), ("baby", ["n"]),
    ("bachelor", ["n"]), ("back", ["ad", "a", "n"]), ("background", ["n"]),
]:
    add(w, p)
add("awake", ["v", "a"], irregulars=["awoke", "awoken"])

# Page 6
add("backward", ["ad"], variants=["backwards"])
for w, p in [
    ("bacon", ["n"]), ("badminton", ["n"]), ("bag", ["n"]), ("baggage", ["n"]),
    ("bakery", ["n"]), ("balance", ["n"]), ("balcony", ["n"]), ("ball", ["n"]),
    ("ballet", ["n"]), ("balloon", ["n"]), ("bamboo", ["n"]), ("ban", ["n", "v"]),
    ("banana", ["n"]), ("band", ["n"]), ("bandage", ["n"]), ("bank", ["n"]),
    ("bar", ["n"]), ("barbecue", ["n"]), ("barber", ["n"]), ("barbershop", ["n"]),
    ("bare", ["a"]), ("bargain", ["n", "v"]), ("bark", ["v", "n"]), ("barrier", ["n"]),
    ("base", ["n"]), ("baseball", ["n"]), ("basement", ["n"]), ("basic", ["a"]),
    ("basin", ["n"]), ("basis", ["n"]), ("basket", ["n"]), ("basketball", ["n"]),
    ("bat", ["n"]), ("bath", ["n"]), ("bathe", ["v"]), ("bathroom", ["n"]),
    ("bathtub", ["n"]), ("battery", ["n"]), ("battle", ["n"]), ("bay", ["n"]),
    ("BC", ["abbr"]), ("beach", ["n"]), ("bean", ["n"]), ("bean curd", ["n"]),
    ("beard", ["n"]), ("beast", ["n"]), ("beautiful", ["a"]), ("beauty", ["n"]),
    ("because", ["conj"]), ("bed", ["n"]), ("beddings", ["n"]), ("bedroom", ["n"]),
    ("bee", ["n"]),
]:
    add(w, p)
add("bacterium", ["n"], irregulars=["bacteria"])
add("bad", ["a"], irregulars=["worse", "worst"])
add("be", ["v"], irregulars=["am", "is", "are", "was", "were", "being", "been"])
add("bear", ["n", "v"])
add("beat", ["v", "n"], irregulars=["beat", "beaten"])
add("become", ["v"], irregulars=["became", "become"])

# Page 7
for w, p in [
    ("beef", ["n"]), ("beer", ["n"]), ("before", ["prep", "ad", "conj"]), ("beg", ["v"]),
    ("behalf", ["n"]), ("behave", ["v"]), ("behind", ["prep", "ad"]), ("being", ["n"]),
    ("belief", ["n"]), ("believe", ["v"]), ("bell", ["n"]), ("belly", ["n"]),
    ("belong", ["v"]), ("below", ["prep"]), ("belt", ["n"]), ("bench", ["n"]),
    ("beneath", ["prep"]), ("beneficial", ["a"]), ("benefit", ["n", "v"]), ("bent", ["a", "n"]),
    ("beside", ["prep"]), ("besides", ["prep", "ad"]), ("betray", ["v"]), ("between", ["prep"]),
    ("beyond", ["prep"]), ("bicycle", ["n"]), ("bid", ["v", "n"]), ("big", ["a"]),
    ("bill", ["n"]), ("bingo", ["n"]), ("biochemistry", ["n"]), ("biography", ["n"]),
    ("biology", ["n"]), ("bird", ["n"]), ("birth", ["n"]), ("birthday", ["n"]),
    ("birthplace", ["n"]), ("biscuit", ["n"]), ("bishop", ["n"]), ("bit", ["n"]),
    ("bitter", ["a"]), ("black", ["a", "n"]), ("blackboard", ["n"]), ("blame", ["n", "v"]),
    ("blank", ["n", "a"]), ("blanket", ["n"]), ("bleed", ["v"]), ("bless", ["v"]),
    ("blind", ["a"]), ("block", ["n", "v"]), ("blood", ["n"]), ("blouse", ["n"]),
    ("blue", ["n", "a"]), ("board", ["n", "v"]), ("boat", ["n"]), ("body", ["n"]),
]:
    add(w, p)
add("begin", ["v"], irregulars=["began", "begun"])
add("behaviour", ["n"], variants=["behavior"])
add("bend", ["v"], irregulars=["bent"])
add("bike", ["n"], variants=["bicycle"])
add("bite", ["v"], irregulars=["bit", "bitten"])
add("blow", ["v"], irregulars=["blew", "blown"])

# Page 8
for w, p in [
    ("boil", ["v"]), ("bomb", ["n", "v"]), ("bond", ["n", "v"]), ("bone", ["n"]),
    ("bonus", ["n"]), ("book", ["n", "v"]), ("boom", ["n", "v"]), ("boot", ["n"]),
    ("booth", ["n"]), ("border", ["n"]), ("bored", ["a"]), ("boring", ["a"]),
    ("born", ["a"]), ("borrow", ["v"]), ("boss", ["n"]), ("botanical", ["a"]),
    ("botany", ["n"]), ("both", ["a", "pron"]), ("bother", ["v"]), ("bottle", ["n"]),
    ("bottom", ["n"]), ("bounce", ["v"]), ("bound", ["a"]), ("boundary", ["n"]),
    ("bow", ["v", "n"]), ("bowl", ["n"]), ("bowling", ["n"]), ("box", ["n"]),
    ("boxing", ["n"]), ("boy", ["n"]), ("boycott", ["v"]), ("brain", ["n"]),
    ("brake", ["n", "v"]), ("branch", ["n"]), ("brand", ["n"]), ("brave", ["a"]),
    ("bravery", ["n"]), ("bread", ["n"]), ("breakfast", ["n"]), ("breakthrough", ["n"]),
    ("breast", ["n"]), ("breath", ["n"]), ("breathe", ["v"]), ("breathless", ["a"]),
    ("brewery", ["n"]), ("brick", ["n"]), ("bride", ["n"]), ("bridegroom", ["n"]),
    ("bridge", ["n"]), ("brief", ["a"]), ("bright", ["a"]), ("brilliant", ["a"]),
    ("broad", ["a"]), ("brochure", ["n"]), ("broken", ["a"]), ("broom", ["n"]),
    ("brother", ["n"]), ("brown", ["n", "a"]),
]:
    add(w, p)
add("break", ["v", "n"], irregulars=["broke", "broken"])
add("bring", ["v"], irregulars=["brought"])
add("broadcast", ["v"], irregulars=["broadcast", "broadcasted"])

# Page 9
for w, p in [
    ("brunch", ["n"]), ("brush", ["v", "n"]), ("Buddhism", ["n"]), ("budget", ["n"]),
    ("buffet", ["n"]), ("building", ["n"]), ("bunch", ["n"]), ("bungalow", ["n"]),
    ("burden", ["n"]), ("bureaucratic", ["a"]), ("burglar", ["n"]), ("burst", ["v"]),
    ("bury", ["v"]), ("bus", ["n"]), ("bush", ["n"]), ("business", ["n"]),
    ("busy", ["a"]), ("but", ["conj", "prep"]), ("butcher", ["n", "v"]), ("butter", ["n"]),
    ("butterfly", ["n"]), ("button", ["n", "v"]), ("by", ["prep"]), ("bye", ["int"]),
    ("cab", ["n"]), ("cabbage", ["n"]), ("cafe", ["n"]), ("cafeteria", ["n"]),
    ("cage", ["n"]), ("cake", ["n"]), ("calculate", ["v"]), ("call", ["n", "v"]),
    ("calm", ["a", "v"]), ("camel", ["n"]), ("camera", ["n"]), ("camp", ["n", "v"]),
    ("campaign", ["n"]), ("canal", ["n"]), ("cancel", ["v"]), ("cancer", ["n"]),
    ("candidate", ["n"]), ("candle", ["n"]), ("candy", ["n"]), ("canteen", ["n"]),
    ("cap", ["n"]), ("capital", ["n"]), ("capsule", ["n"]), ("captain", ["n"]),
    ("caption", ["n"]), ("car", ["n"]), ("carbon", ["n"]),
]:
    add(w, p)
add("build", ["v"], irregulars=["built"])
add("burn", ["v", "n"], irregulars=["burnt", "burned"])
add("businessman", ["n"], variants=["businesswoman"], irregulars=["businessmen", "businesswomen"])
add("buy", ["v"], irregulars=["bought"])
add("can", ["v", "n"], irregulars=["could"])
add("can't", ["v"], variants=["cannot"])

# Page 10
for w, p in [
    ("card", ["n"]), ("care", ["n", "v"]), ("careful", ["a"]), ("careless", ["a"]),
    ("carpenter", ["n"]), ("carpet", ["n"]), ("carriage", ["n"]), ("carrier", ["n"]),
    ("carrot", ["n"]), ("carry", ["v"]), ("cartoon", ["n"]), ("carve", ["v"]),
    ("case", ["n"]), ("cash", ["n", "v"]), ("cassette", ["n"]), ("castle", ["n"]),
    ("casual", ["a"]), ("cat", ["n"]), ("catalogue", ["n"]), ("catastrophe", ["n"]),
    ("category", ["n"]), ("cater", ["v"]), ("Catholic", ["a"]), ("cattle", ["n"]),
    ("cause", ["n", "v"]), ("caution", ["n"]), ("cautious", ["a"]), ("cave", ["n"]),
    ("ceiling", ["n"]), ("celebrate", ["v"]), ("celebration", ["n"]), ("cell", ["n"]),
    ("cent", ["n"]), ("centigrade", ["a"]), ("central", ["a"]), ("century", ["n"]),
    ("ceremony", ["n"]), ("certain", ["a"]), ("certificate", ["n"]), ("chain", ["n"]),
    ("chair", ["n"]), ("chalk", ["n"]), ("challenge", ["n"]), ("challenging", ["a"]),
    ("champion", ["n"]), ("chance", ["n"]), ("change", ["n", "v"]), ("changeable", ["a"]),
    ("channel", ["n"]), ("chant", ["v", "n"]), ("chaos", ["n"]), ("chapter", ["n"]),
    ("character", ["n"]), ("characteristic", ["a", "n"]),
]:
    add(w, p)
add("cast", ["v"], irregulars=["cast"])
add("catch", ["v"], irregulars=["caught"])
add("CD", ["n"], variants=["compact disk"])
add("centimetre", ["n"], variants=["centimeter"])
add("centre", ["n"], variants=["center"])
add("chairman", ["n"], variants=["chairwoman"], irregulars=["chairmen", "chairwomen"])

# Page 11
for w, p in [
    ("charge", ["v", "n"]), ("chart", ["n"]), ("chat", ["n", "v"]), ("cheap", ["a"]),
    ("cheat", ["n", "v"]), ("check", ["n", "v"]), ("cheek", ["n"]), ("cheer", ["n", "v"]),
    ("cheerful", ["a"]), ("cheers", ["int"]), ("cheese", ["n"]), ("chef", ["n"]),
    ("chemical", ["a", "n"]), ("chemist", ["n"]), ("chemistry", ["n"]), ("chess", ["n"]),
    ("chest", ["n"]), ("chew", ["v"]), ("chicken", ["n"]), ("chief", ["a", "n"]),
    ("childhood", ["n"]), ("chocolate", ["n"]), ("choice", ["n"]), ("choir", ["n"]),
    ("choke", ["n", "v"]), ("chopsticks", ["n"]), ("chorus", ["n"]), ("Christian", ["n"]),
    ("Christmas", ["n"]), ("church", ["n"]), ("cigar", ["n"]), ("cigarette", ["n"]),
    ("cinema", ["n"]), ("circle", ["n", "v"]), ("circuit", ["n"]), ("circulate", ["v"]),
    ("circumstance", ["n"]), ("circus", ["n"]), ("citizen", ["n"]), ("city", ["n"]),
    ("civil", ["a"]), ("civilian", ["n"]), ("civilization", ["n"]), ("clap", ["v"]),
    ("clarify", ["v"]), ("class", ["n"]), ("classic", ["a"]), ("classify", ["v"]),
    ("classmate", ["n"]), ("classroom", ["n"]), ("claw", ["n"]), ("clay", ["n"]),
    ("clean", ["v", "a"]), ("cleaner", ["n"]), ("clear", ["a"]), ("clerk", ["n"]),
    ("clever", ["a"]), ("click", ["v"]), ("climate", ["n"]),
]:
    add(w, p)
add("cheque", ["n"], variants=["check"])
add("child", ["n"], irregulars=["children"])
add("choose", ["v"], irregulars=["chose", "chosen"])

# Page 12
for w, p in [
    ("climb", ["v"]), ("clinic", ["n"]), ("clock", ["n"]), ("clone", ["v"]),
    ("close", ["a", "ad"]), ("cloth", ["n"]), ("clothes", ["n"]), ("clothing", ["n"]),
    ("cloud", ["n"]), ("cloudy", ["a"]), ("club", ["n"]), ("clumsy", ["a"]),
    ("coach", ["n"]), ("coal", ["n"]), ("coast", ["n"]), ("coat", ["n"]),
    ("cocoa", ["n"]), ("coffee", ["n"]), ("coin", ["n"]), ("coincidence", ["n"]),
    ("coke", ["n"]), ("cold", ["a", "n"]), ("collar", ["n"]), ("colleague", ["n"]),
    ("collect", ["v"]), ("collection", ["n"]), ("college", ["n"]), ("collision", ["n"]),
    ("comb", ["n", "v"]), ("combine", ["v"]), ("comedy", ["n"]), ("comfort", ["n"]),
    ("comfortable", ["a"]), ("command", ["n", "v"]), ("comment", ["n"]),
    ("commercial", ["a"]), ("commit", ["v"]), ("commitment", ["n"]), ("committee", ["n"]),
    ("common", ["a"]), ("communicate", ["v"]), ("communication", ["n"]),
    ("communism", ["n"]), ("communist", ["n", "a"]), ("companion", ["n"]),
    ("company", ["n"]), ("compare", ["v"]), ("compass", ["n"]), ("compensate", ["v"]),
    ("compete", ["v"]), ("competence", ["n"]), ("competition", ["n"]),
    ("complete", ["a", "v"]), ("complex", ["a", "n"]), ("component", ["n"]),
    ("composition", ["n"]), ("comprehension", ["n"]), ("compromise", ["v"]),
    ("compulsory", ["a"]), ("computer", ["n"]),
]:
    add(w, p)
add("colour", ["n", "v"], variants=["color"])
add("come", ["v"], irregulars=["came", "come"])

# Page 13
for w, p in [
    ("concentrate", ["v"]), ("concept", ["n"]), ("concern", ["v", "n"]), ("concert", ["n"]),
    ("conclude", ["v"]), ("conclusion", ["n"]), ("concrete", ["a"]), ("condemn", ["v"]),
    ("condition", ["n"]), ("conduct", ["v"]), ("conductor", ["n"]), ("conference", ["n"]),
    ("confident", ["a"]), ("confidential", ["a"]), ("confirm", ["v"]), ("conflict", ["n"]),
    ("confuse", ["v"]), ("congratulate", ["v"]), ("congratulation", ["n"]), ("connect", ["v"]),
    ("connection", ["n"]), ("conscience", ["n"]), ("consensus", ["n"]), ("consequence", ["n"]),
    ("conservation", ["n"]), ("conservative", ["a"]), ("consider", ["v"]),
    ("considerate", ["a"]), ("consideration", ["n"]), ("consist", ["v"]),
    ("consistent", ["a"]), ("constant", ["a"]), ("constitution", ["n"]),
    ("construct", ["v"]), ("construction", ["n"]), ("consult", ["v"]),
    ("consultant", ["n"]), ("consume", ["v"]), ("contain", ["v"]), ("container", ["n"]),
    ("contemporary", ["a"]), ("content", ["n", "a"]), ("continent", ["n"]),
    ("continue", ["v"]), ("contradict", ["v"]), ("contradictory", ["a"]),
    ("contrary", ["n", "a"]), ("contribute", ["v"]), ("contribution", ["n"]),
    ("control", ["v", "n"]), ("controversial", ["a"]), ("convenience", ["n"]),
    ("convenient", ["a"]), ("conventional", ["a"]), ("conversation", ["n"]),
    ("convey", ["v"]), ("convince", ["v"]), ("cook", ["n", "v"]), ("cooker", ["n"]),
    ("cookie", ["n"]), ("cool", ["a"]),
]:
    add(w, p)

# Page 14
for w, p in [
    ("copy", ["n", "v"]), ("corn", ["n"]), ("corner", ["n"]), ("corporation", ["n"]),
    ("correct", ["v", "a"]), ("correction", ["n"]), ("correspond", ["v"]),
    ("corrupt", ["a", "v"]), ("cost", ["n", "v"]), ("cottage", ["n"]),
    ("cotton", ["n", "a"]), ("cough", ["n", "v"]), ("could", ["v"]), ("count", ["v"]),
    ("counter", ["n"]), ("country", ["n"]), ("countryside", ["n"]), ("couple", ["n"]),
    ("courage", ["n"]), ("course", ["n"]), ("court", ["n"]), ("courtyard", ["n"]),
    ("cousin", ["n"]), ("cover", ["n", "v"]), ("cow", ["n"]), ("crash", ["v", "n"]),
    ("crayon", ["n"]), ("crazy", ["a"]), ("cream", ["n"]), ("create", ["v"]),
    ("creature", ["n"]), ("credit", ["n"]), ("crew", ["n"]), ("crime", ["n"]),
    ("criminal", ["n"]), ("crop", ["n"]), ("cross", ["n", "v"]), ("crossing", ["n"]),
    ("crossroads", ["n"]), ("crowd", ["n", "v"]), ("cruel", ["a"]), ("cry", ["n", "v"]),
    ("cube", ["n"]), ("cubic", ["a"]), ("cuisine", ["n"]), ("culture", ["n"]),
    ("cup", ["n"]), ("cupboard", ["n"]), ("cure", ["n", "v"]), ("curious", ["a"]),
    ("currency", ["n"]), ("curriculum", ["n"]), ("curtain", ["n"]), ("cushion", ["n"]),
    ("custom", ["n"]), ("customer", ["n"]), ("customs", ["n"]), ("cycle", ["v"]),
    ("cyclist", ["n"]),
]:
    add(w, p)
add("cosy", ["a"], variants=["cozy"])
add("criterion", ["n"], irregulars=["criteria"])
add("cut", ["v", "n"], irregulars=["cut"])

# Page 15
add("dad", ["n"], variants=["daddy"])
for w, p in [
    ("daily", ["a", "ad", "n"]), ("dam", ["n"]), ("damage", ["n", "v"]), ("damp", ["a", "n"]),
    ("dance", ["n", "v"]), ("danger", ["n"]), ("dangerous", ["a"]), ("dare", ["v"]),
    ("dark", ["a", "n"]), ("darkness", ["n"]), ("dash", ["v", "n"]), ("data", ["n"]),
    ("database", ["n"]), ("date", ["n", "v"]), ("daughter", ["n"]), ("dawn", ["n"]),
    ("day", ["n"]), ("dead", ["a"]), ("deadline", ["n"]), ("deaf", ["a"]),
    ("deal", ["n"]), ("dear", ["a"]), ("death", ["n"]), ("debate", ["n", "v"]),
    ("debt", ["n"]), ("decade", ["n"]), ("decide", ["v"]), ("decision", ["n"]),
    ("declare", ["v"]), ("decline", ["v"]), ("decorate", ["v"]), ("decoration", ["n"]),
    ("decrease", ["v"]), ("deed", ["n"]), ("deep", ["a", "ad"]), ("deer", ["n"]),
    ("defeat", ["v"]), ("defend", ["v"]), ("degree", ["n"]), ("delay", ["n", "v"]),
    ("delete", ["v", "n"]), ("deliberately", ["ad"]), ("delicate", ["a"]),
    ("delicious", ["a"]), ("delight", ["n"]), ("delighted", ["a"]), ("deliver", ["v"]),
    ("demand", ["v"]), ("dentist", ["n"]), ("departure", ["n"]), ("depend", ["v"]),
    ("deposit", ["v", "n"]), ("depth", ["n"]), ("describe", ["v"]),
    ("description", ["n"]), ("desert", ["v", "n"]), ("deserve", ["v"]),
]:
    add(w, p)
add("defence", ["n"], variants=["defense"])
add("department", ["n"], variants=["Dept."])

# Page 16
for w, p in [
    ("design", ["v", "n"]), ("desire", ["v", "n"]), ("desk", ["n"]), ("desperate", ["a"]),
    ("dessert", ["n"]), ("destination", ["n"]), ("destroy", ["v"]), ("detective", ["n"]),
    ("determine", ["v"]), ("develop", ["v"]), ("development", ["n"]), ("devote", ["v"]),
    ("devotion", ["n"]), ("diagram", ["n"]), ("dial", ["v"]), ("diamond", ["n"]),
    ("diary", ["n"]), ("dictation", ["n"]), ("dictionary", ["n"]), ("die", ["v"]),
    ("diet", ["n"]), ("differ", ["v"]), ("difference", ["n"]), ("different", ["a"]),
    ("difficult", ["a"]), ("difficulty", ["n"]), ("digest", ["v"]), ("digital", ["a"]),
    ("dignity", ["n"]), ("dilemma", ["n"]), ("dimension", ["n"]), ("dinner", ["n"]),
    ("dinosaur", ["n"]), ("dioxide", ["n"]), ("dip", ["v"]), ("diploma", ["n"]),
    ("direct", ["a", "v"]), ("direction", ["n"]), ("director", ["n"]),
    ("directory", ["n"]), ("dirty", ["a"]), ("disability", ["n"]), ("disabled", ["a"]),
    ("disadvantage", ["n"]), ("disagree", ["v"]), ("disagreement", ["n"]),
    ("disappear", ["v"]), ("disappoint", ["v"]), ("disappointed", ["a"]),
    ("disaster", ["n"]), ("discount", ["n"]), ("discourage", ["v"]), ("discover", ["v"]),
    ("discovery", ["n"]), ("discrimination", ["n"]), ("discuss", ["v"]),
    ("discussion", ["n"]), ("disease", ["n"]), ("disgusting", ["a"]), ("dish", ["n"]),
]:
    add(w, p)
add("dialogue", ["n"], variants=["dialog"])
add("dig", ["v"], irregulars=["dug"])

# Page 17
add("disk", ["n"], variants=["disc"])
for w, p in [
    ("dislike", ["v"]), ("dismiss", ["v"]), ("distance", ["n"]), ("distant", ["a"]),
    ("distinction", ["n"]), ("distinguish", ["v"]), ("distribute", ["v"]),
    ("district", ["n"]), ("disturb", ["v"]), ("disturbing", ["a"]), ("dive", ["v"]),
    ("diverse", ["a"]), ("divide", ["v"]), ("division", ["n"]), ("divorce", ["v"]),
    ("dizzy", ["a"]), ("doctor", ["n"]), ("document", ["n"]), ("dog", ["n"]),
    ("doll", ["n"]), ("dollar", ["n"]), ("donate", ["v"]), ("door", ["n"]),
    ("dot", ["n"]), ("double", ["a", "n"]), ("doubt", ["n", "v"]), ("down", ["prep", "ad"]),
    ("download", ["n", "v"]), ("downstairs", ["ad"]), ("downtown", ["ad", "n", "a"]),
    ("dozen", ["n"]), ("draft", ["n", "v"]), ("drag", ["v"]), ("drawback", ["n"]),
    ("drawer", ["n"]), ("dress", ["n", "v"]), ("drill", ["n", "v"]), ("driver", ["n"]),
    ("drop", ["n", "v"]), ("drug", ["n"]), ("drum", ["n"]), ("drunk", ["a"]),
    ("dry", ["v", "a"]), ("duck", ["n"]), ("due", ["a"]), ("dull", ["a"]),
    ("dumpling", ["n"]), ("during", ["prep"]), ("dusk", ["n"]), ("dust", ["n"]),
    ("dustbin", ["n"]), ("dusty", ["a"]), ("duty", ["n"]),
]:
    add(w, p)
add("do", ["v"], irregulars=["did", "done"])
add("dormitory", ["n"], variants=["dorm"])
add("Dr", ["n"], variants=["doctor"])
add("draw", ["v"], irregulars=["drew", "drawn"])
add("dream", ["n", "v"], irregulars=["dreamt", "dreamed"])
add("drink", ["v"], irregulars=["drank", "drunk"])
add("drive", ["v"], irregulars=["drove", "driven"])

# Page 18
add("DVD", ["n"], variants=["digital versatile disk"])
for w, p in [
    ("dynamic", ["a"]), ("dynasty", ["n"]), ("each", ["a", "pron"]), ("eager", ["a"]),
    ("eagle", ["n"]), ("ear", ["n"]), ("early", ["a", "ad"]), ("earn", ["v"]),
    ("earth", ["n"]), ("earthquake", ["n"]), ("east", ["a", "ad", "n"]), ("Easter", ["n"]),
    ("eastern", ["a"]), ("easy", ["a"]), ("ecology", ["n"]), ("edge", ["n"]),
    ("edition", ["n"]), ("editor", ["n"]), ("educate", ["v"]), ("education", ["n"]),
    ("educator", ["n"]), ("effect", ["n"]), ("effort", ["n"]), ("egg", ["n"]),
    ("eggplant", ["n"]), ("either", ["a", "conj", "ad"]), ("elder", ["n"]),
    ("elect", ["v"]), ("electric", ["a"]), ("electrical", ["a"]), ("electricity", ["n"]),
    ("electronic", ["a"]), ("elegant", ["a"]), ("elephant", ["n"]), ("else", ["ad"]),
    ("e-mail", ["n", "v"]), ("embarrass", ["v"]), ("embassy", ["n"]),
    ("emergency", ["n"]), ("emperor", ["n"]), ("employ", ["v"]), ("empty", ["a"]),
    ("encourage", ["v"]), ("encouragement", ["n"]), ("end", ["n", "v"]), ("ending", ["n"]),
    ("endless", ["a"]), ("enemy", ["n"]), ("energetic", ["a"]), ("energy", ["n"]),
    ("engine", ["n"]), ("engineer", ["n"]), ("enjoy", ["v"]), ("enjoyable", ["a"]),
    ("enlarge", ["v"]), ("enough", ["pron", "a", "ad"]), ("enquiry", ["n"]), ("enter", ["v"]),
]:
    add(w, p)
add("eat", ["v"], irregulars=["ate", "eaten"])

# Page 19
add("exam", ["n"], variants=["examination"])
for w, p in [
    ("enterprise", ["n"]), ("entertainment", ["n"]), ("enthusiastic", ["a"]),
    ("entire", ["a"]), ("entrance", ["n"]), ("entry", ["n"]), ("envelope", ["n"]),
    ("environment", ["n"]), ("envy", ["v", "n"]), ("equal", ["a", "v"]),
    ("equality", ["n"]), ("equip", ["v"]), ("equipment", ["n"]), ("eraser", ["n"]),
    ("error", ["n"]), ("erupt", ["v"]), ("escape", ["n", "v"]), ("especially", ["ad"]),
    ("essay", ["n"]), ("Europe", ["n"]), ("European", ["a", "n"]), ("evaluate", ["v"]),
    ("even", ["ad"]), ("evening", ["n"]), ("event", ["n"]), ("eventually", ["ad"]),
    ("ever", ["ad"]), ("every", ["a"]), ("everybody", ["pron"]), ("everyday", ["a"]),
    ("everyone", ["pron"]), ("everything", ["pron"]), ("everywhere", ["ad"]),
    ("evidence", ["n"]), ("evident", ["a"]), ("evolution", ["n"]), ("exact", ["a"]),
    ("examine", ["v"]), ("example", ["n"]), ("excellent", ["a"]), ("except", ["prep"]),
    ("exchange", ["n", "v"]), ("excite", ["v"]), ("excuse", ["n", "v"]),
    ("exercise", ["n", "v"]), ("exhibition", ["n"]), ("exist", ["v"]),
    ("existence", ["n"]), ("exit", ["n"]), ("expand", ["v"]), ("expect", ["v"]),
    ("expectation", ["n"]), ("expense", ["n"]), ("expensive", ["a"]),
    ("experience", ["n"]), ("experiment", ["n"]), ("expert", ["n"]),
    ("explain", ["v"]), ("explanation", ["n"]), ("explicit", ["a"]), ("explode", ["v"]),
]:
    add(w, p)

# Page 20
for w, p in [
    ("explore", ["v"]), ("export", ["n", "v"]), ("expose", ["v"]), ("express", ["v", "n"]),
    ("expression", ["n"]), ("extension", ["n"]), ("extra", ["a"]), ("extraordinary", ["a"]),
    ("extreme", ["a"]), ("eye", ["n"]), ("eyesight", ["n"]), ("face", ["n", "v"]),
    ("facial", ["a"]), ("fact", ["n"]), ("factory", ["n"]), ("fade", ["v"]),
    ("fail", ["v", "n"]), ("failure", ["n"]), ("fair", ["a", "n"]), ("faith", ["n"]),
    ("false", ["a"]), ("familiar", ["a"]), ("family", ["n"]), ("famous", ["a"]),
    ("fan", ["n"]), ("fancy", ["n", "v", "a"]), ("fantastic", ["a"]), ("fantasy", ["n"]),
    ("fare", ["n"]), ("farm", ["n"]), ("farmer", ["n"]), ("fast", ["a", "ad"]),
    ("fasten", ["v"]), ("fat", ["n", "a"]), ("father", ["n"]), ("fault", ["n"]),
    ("fax", ["n", "v"]), ("fear", ["n"]), ("feast", ["n"]), ("feather", ["n"]),
    ("federal", ["a"]), ("fee", ["n"]), ("feeling", ["n"]), ("fellow", ["n"]),
    ("female", ["a", "n"]), ("fence", ["n"]), ("ferry", ["n"]), ("festival", ["n", "a"]),
    ("fetch", ["v"]), ("fever", ["n"]), ("few", ["pron", "a"]),
]:
    add(w, p)
add("fall", ["v", "n"], irregulars=["fell", "fallen"], variants=["autumn"])
add("far", ["a", "ad"], irregulars=["farther", "farthest", "further", "furthest"])
add("favour", ["n"], variants=["favor"])
add("favourite", ["a", "n"], variants=["favorite"])
add("feed", ["v"], irregulars=["fed"])
add("feel", ["v"], irregulars=["felt"])

with open("vocab_pages_1_20.json", "w", encoding="utf-8") as f:
    json.dump(entries, f, ensure_ascii=False, separators=(",", ":"))

print(len(entries))
