# Guía de estilo para traducir Night Call al español

Juego noir: taxista nocturno en París, pasajeros con historias íntimas, asesinos en serie.
Tono literario, contenido, humano.

## Flujo de trabajo
1. `PYTHONIOENCODING=utf-8 python tools/batch.py export <objeto> --size 400` → crea `work/<objeto>.in.txt`.
2. Abrir `work/<objeto>.in.txt`. Formato: `== passage`, luego `N TAG | texto`. TAG: `N` narración, `NOMBRE` diálogo de ese personaje, `C->link` opción del jugador, `UI.X` interfaz. Un emote como `:silence:` al inicio del texto NO se traduce ni se copia.
3. Escribir `work/<objeto>.out.tsv`: una línea por fila, `N<TAB>traducción`. Traducir solo el texto después de `| ` (sin nombre de hablante, sin emote).
4. `PYTHONIOENCODING=utf-8 python tools/batch.py import <objeto>`.
5. Repetir 1–4 hasta que export diga "nada pendiente".
6. Validar y corregir cualquier error: `PYTHONIOENCODING=utf-8 python tools/generate.py` (o `tools/validate.py` si no tenés `source/` local).
7. Nunca commitear `work/` ni `build/`. Commits solo con el mensaje, sin líneas `Co-Authored-By`.

## Reglas obligatorias
- **Tú** en todo el juego; **usted** solo si el original marca formalidad (Sir, Madam, Monsieur). Plural: **ustedes** (nunca vosotros/os).
- **Comillas: las mismas que el original, en la misma posición** (“ ” o « » o " "). No agregar comillas a narración que no las tiene. El validador falla si cambian.
- ¿ ¡ obligatorios. Puntos suspensivos: el mismo carácter del original (… o ...).
- Conservar `{variables}`, `<tags>`, `%x%`, `\n` exactamente.
- Español neutro. Evitar: coger, vale, guay, che, ahorita, tío (=amigo), "vosotros", "apuro" (usar prisa), "contextura" (usar complexión).
- El protagonista (el jugador, "you") es hombre: concordar en masculino ("estás cansado").
- Género de cada personaje: `translation/characters.json` (M/F/N). "Your passenger" = "tu pasajero" o "tu pasajera" según quién sea. Ultra Rojo es neutro a propósito: evitar marcarle género. Verificar con `python tools/check_gender.py`.
- Opciones entre paréntesis en infinitivo: (Say nothing.) → (No decir nada.), (Wait.) → (Esperar.).
- Opciones cortas: no mucho más largas que el inglés.
- UI y pistas (clues) en estilo telegráfico como el original: sin agregar artículos ("Victims = wealthy" → "Víctimas = adineradas").
- Nombres propios y lugares de París sin traducir (Hervé, Bois-de-Vincennes).
- Traducción natural, no literal: adaptar expresiones y humor; mantener el registro de cada personaje (jerga, edad, clase social).
- Nunca editar `db/` a mano ni reescribir filas `locked` o `TESTED`.
- Los IDs, links, comandos `$$`, emotes y nombres de hablante nunca se traducen.

## Glosario
cab/taxi → taxi · car → auto (no coche/carro) · cabbie → taxista · fare (dinero) → tarifa · passenger → pasajero/pasajera · client → cliente · cop → policía (no poli/tira/cana) · the Judge → el Juez · the Sandman → el Hombre de Arena · the Angel of Death → el Ángel de la Muerte · Commissioner (Fragonard) → comisario (es un hombre) · suspect → sospechoso · clue → pista · shift → turno · gas station → gasolinera
