# Night Call: Traducción al español (no oficial)

Localización fan, no oficial, de **Night Call** (Monkey Moon / BlackMuffin, publicado por Raw Fury) mediante un plugin de BepInEx. El juego y sus textos pertenecen a sus titulares.

## Instalación (jugadores)

1. Descarga `NightCallEspanol_vX.Y.Z.zip` desde la [última versión (Releases)](../../releases/latest) de este repositorio y descomprímelo.
2. Ejecuta `NightCallEspanol_Setup.exe` y sigue el asistente (Siguiente → elegir carpeta → Instalar → Finalizar). Detecta tu instalación de Night Call sola (Steam); si no la encuentra, te deja elegir la carpeta a mano.
3. Si no tienes [BepInEx](https://github.com/BepInEx/BepInEx) instalado (o está incompleto), el instalador lo instala junto con la traducción; no hace falta instalarlo por separado.
4. Abre el juego. La traducción reemplaza al inglés: deja el idioma del juego en English (el que viene por defecto).

**Para actualizar:** instala la versión nueva encima; no hace falta desinstalar antes.

**Para desinstalar:** desde "Agregar o quitar programas" de Windows, busca "Night Call - Traducción al español" (o ejecuta `unins000.exe` en la carpeta del juego). Quita la traducción sin tocar tus partidas guardadas; si BepInEx ya estaba instalado antes, tampoco lo toca.

¿Prefieres un instalador por consola en vez del asistente gráfico? En el mismo zip está `NightCallEspanol_Instalador_Consola.exe`, con el mismo resultado y sin ventanas. Usa siempre el mismo instalador para instalar, actualizar y desinstalar.

Requiere Windows. El instalador no modifica archivos del juego en sí, solo agrega un plugin de BepInEx y reemplaza los textos de UI/diálogos por su traducción.

## Cómo está construido

| Capa | Tecnología | Qué hace |
|---|---|---|
| Motor del juego | **Unity 2018.4** (runtime **Mono**) | Ejecuta el juego; carga diálogos y UI como objetos en memoria |
| Carga del mod | **Unity Doorstop** (`winhttp.dll` + `doorstop_config.ini`) | Se inyecta al arrancar el juego y carga BepInEx antes que el código del juego |
| Framework de mods | **BepInEx 5.4.23** | Carga el plugin, maneja su configuración (`BepInEx/config`) y el log (`BepInEx/LogOutput.log`) |
| Parches en tiempo real | **HarmonyX** (`0Harmony.dll`) + **MonoMod** | Intercepta métodos del juego sin modificar sus archivos |
| Plugin de traducción | `NightCallSpanish.dll` (C#, .NET Framework 4.6) | Reemplaza los textos por su versión en español |
| Texto en pantalla | **TextMeshPro** y `UnityEngine.UI.Text` | Donde el plugin traduce los textos sueltos que se muestran |

**Qué intercepta el plugin:**
- **Diálogos (Prompter):** el juego guarda cada conversación en objetos `NC.Dialogs.DialogObjectScript` con passages (`Prompter.Runtime.PassageSection`) y opciones (`ChoiceSection`). Al cargar cada escena, el plugin reemplaza las líneas de cada passage por las de `Spanish_Texts/`, conservando comandos (`$$ … $$`), links y nombres de hablante.
- **Guiones de texto (TextAsset):** la intro, la radio, los periódicos, la gasolinera, los lugares de los casos y el final son guiones fuente; el parche de `TextAsset.text` entrega la versión en español.
- **Interfaz (LocalizationManager):** las claves de UI (`UI.MENU.NEW`, …) se traducen desde `Spanish_UI/key_based_translations.json`.
- **Respaldo (TextMeshPro):** el parche de `TMP_Text.text` traduce cualquier texto suelto que quede, usando `Spanish_UI/full_translation_mapping.json`.
- Configuración en `BepInEx/config/com.nightcall.spanish.cfg`: capas activables una por una, reemplazo de fuentes (apagado: las fuentes del juego ya soportan á é í ó ú ñ ¿ ¡) y la tecla **F5** para recargar la traducción sin reiniciar.

## Aspectos técnicos

El juego guarda sus diálogos y textos de interfaz en archivos que el motor (Unity) lee en tiempo de ejecución. La traducción funciona en dos partes:

- **Un plugin de BepInEx** (`src/Mod`, en C#) que intercepta el texto del juego antes de que se muestre en pantalla y lo reemplaza por su versión en español, sin tocar el juego original.
- **Una base de datos propia** (`db/`, ~28.940 filas en formato JSONL, una por cada línea de texto visible) que es la fuente de verdad de la traducción, separada del código del juego.

Cada fila conserva metadatos para no romper el juego al traducir: qué personaje habla, qué opción de diálogo lleva a qué escena, y todos los `{placeholders}`, `<tags>` y variables que el motor necesita intactos.

## Historia del proyecto

Esta traducción no se hizo de un tirón. Arrancó, se dejó a medias por un buen tiempo, y se retomó después. Entre el primer intento y esta versión terminada pasaron cerca de 5 años.

## Desafíos de la traducción

- Volver después de tanto tiempo significó reconstruir el contexto: revisar qué estaba traducido y qué no, si el criterio de traducción de años atrás seguía siendo el que quería usar, y parchear inconsistencias entre lo viejo y lo nuevo antes de seguir.
- Con la traducción hecha en tandas separadas por años, mantener el mismo tono y las mismas decisiones de estilo (tuteo, glosario, cómo se traduce cada personaje) para que no se note dónde para una etapa y arranca la otra.
- Entre el primer intento y la vuelta al proyecto, hubo que revisar si algo del juego había cambiado (parches, actualizaciones) que pudiera desactualizar lo ya traducido.
- Cada línea traducida tiene que conservar exactamente los mismos marcadores, comillas y saltos de línea que el original, porque el motor los usa para armar la escena y no son solo texto.
- En promedio, una traducción al español es entre 20% y 40% más larga que el inglés original. En los botones de diálogo y las tarjetas de pistas de investigación, eso puede desbordar el espacio disponible en pantalla, así que hubo que revisar y reformular cientos de líneas para que dijeran lo mismo con menos palabras, sin perder matices.
- Mantener el mismo tono (noir, literario), el mismo trato (tuteo salvo formalidad explícita del original) y el mismo estilo telegráfico en la interfaz y las pistas (sin agregar artículos que el original no tiene) a lo largo de todo el juego, incluyendo decenas de personajes secundarios con voces propias.
- El inglés no marca género en la segunda persona; el español sí. Hubo que fijar una convención (protagonista masculino) y aplicarla consistente en todo el diálogo.
- Nombres propios y lugares de París (Hervé, Bois-de-Vincennes) se mantienen sin traducir a propósito, para conservar la ambientación.

## Para desarrolladores / traductores

La fuente de verdad de la traducción es `db/` (JSONL, una fila por texto visible del juego).

```
source/ (volcado del juego) → tools/extract.py → db/ → traducción (tools/batch.py, tools/tm.py)
→ tools/generate.py (+ validate) → build/data → tools/install.py → juego (F5 recarga)
```

- `db/dialogs/<objeto>.jsonl`, `db/ui.jsonl`: base de traducción (status TODO/TRANSLATED/REVIEW/TESTED, `locked`)
- `tools/`: extract, batch (export/import), tm (memoria), validate, generate, install, build_release, report, port_plugin
- `translation/TRANSLATOR.md`: guía de estilo y glosario
- `src/Mod`: plugin BepInEx (generado con `tools/port_plugin.py`, ver Licencias); `src/Dumper`: volcador del texto original
- No están en git: `source/` (texto original del juego), `build/`, `work/`, `ref-russian/`, `backups/`

Reglas: nunca editar `db/` a mano ni reescribir filas `locked` o `TESTED`; los IDs, links, comandos
`$$`, emotes y nombres de hablante nunca se traducen.

Para armar el instalador distribuible: `tools/build_release.py` (requiere `pip install pyinstaller`
e Inno Setup, más una instalación local con BepInEx + el plugin compilado en Release).

## Licencias

- [BepInEx](https://github.com/BepInEx/BepInEx) (LGPL-2.1), [HarmonyX](https://github.com/BepInEx/HarmonyX) (MIT) y [MonoMod](https://github.com/MonoMod/MonoMod) (MIT), incluidos en el instalador.
- El plugin deriva de [russian-localisation-night-call](https://github.com/4RH1T3CT0R7/russian-localisation-night-call) de Artem Lytkin (4RH1T3CT0R), bajo [CC BY 4.0](https://github.com/4RH1T3CT0R7/russian-localisation-night-call/blob/main/LICENSE) (atribución obligatoria; uso no comercial sin permiso del autor). **Modificado** para el español: textos, detección de traducciones, fuentes y herramientas propias.
