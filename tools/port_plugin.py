"""Genera src/Mod/SpanishLocalization.cs a partir del plugin ruso (ref-russian/).

Cambios mínimos y verificados (cada reemplazo debe aplicarse, si no falla):
  - nombres: namespace, clase, GUID/Harmony id, carpetas Spanish_UI/Spanish_Texts, sufijo _spa
  - "ya traducido": los chequeos de cirílico pasan a IsTranslated() (HashSet de textos españoles)
  - búsqueda de passages: primero objeto exacto (001_patricia_02), luego base, luego título
  - fuentes: reemplazo de fuentes/SDF desactivado por config (Font/EnableFontReplacement=false)
  - sin " km" -> " км" ni quitado de mayúsculas
Uso: python tools/port_plugin.py
"""
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "ref-russian", "src", "Mod")
DST = os.path.join(ROOT, "src", "Mod")


def sub(s, pattern, repl, count=1, regex=False):
    n = len(re.findall(pattern, s)) if regex else s.count(pattern)
    if n < count:
        raise SystemExit(f"no se encontró ({n}/{count}): {pattern[:80]!r}")
    return re.sub(pattern, repl, s) if regex else s.replace(pattern, repl)


def port_cs(s):
    s = sub(s, "NightCallRussian", "NightCallSpanish")
    s = sub(s, "RussianLocalization", "SpanishLocalization", count=10)
    s = sub(s, '"com.nightcall.russian", "Night Call Russian", "8.1.0"',
            '"com.nightcall.spanish", "Night Call Spanish", "0.1.0"')
    s = sub(s, 'new Harmony("com.nightcall.russian")', 'new Harmony("com.nightcall.spanish")')
    s = sub(s, "Night Call Russian Localization v8.1.0", "Night Call Spanish Localization v0.1.0")
    s = sub(s, '"Russian_UI"', '"Spanish_UI"', count=2)
    s = sub(s, '"Russian_Texts"', '"Spanish_Texts"', count=2)
    s = sub(s, '"Russian_Texts_backup"', '"Spanish_Texts_backup"')
    s = sub(s, '.Replace("_rus", "_eng")', '.Replace("_spa", "_eng")')
    s = sub(s, '.Replace("_rus", "")', '.Replace("_spa", "")', count=2)
    s = sub(s, '"*_rus.txt"', '"*_spa.txt"')
    s = sub(s, 'value = value.Replace(" km", " км");', "// (español: los km se muestran igual)")

    # --- "ya traducido": HashSet de salidas españolas en lugar de detectar cirílico ---
    s = sub(s, "internal static Dictionary<string, string> RuToEngSpeaker = new Dictionary<string, string>();",
            "internal static Dictionary<string, string> RuToEngSpeaker = new Dictionary<string, string>();\n"
            "        // Textos españoles conocidos: si un texto ya está acá, no se vuelve a traducir.\n"
            "        internal static HashSet<string> SpanishValues = new HashSet<string>();\n"
            "        internal static bool IsTranslated(string text)\n"
            "        {\n"
            "            return !string.IsNullOrEmpty(text) && SpanishValues.Contains(text.Trim());\n"
            "        }")
    s = sub(s, r"// Check if already contains Cyrillic\s*foreach \(char c in text\)\s*\{\s*if \(c >= 0x0400 && c <= 0x04FF\) return null;\s*\}",
            "if (IsTranslated(text)) return null;", regex=True)
    s = sub(s, r"foreach \(char ch in part\)\s*\{\s*if \(ch >= 0x0400 && ch <= 0x04FF\) \{ hasCyr = true; break; \}\s*\}",
            "hasCyr = IsTranslated(part);", regex=True)
    s = sub(s, "foreach (char c in value) { if (c >= 0x0400 && c <= 0x04FF) { hasCyr = true; break; } }",
            "hasCyr = IsTranslated(value) || SpanishValues.Contains(value);")
    # El juego muestra ciertos textos en MAYÚSCULAS: en español se conserva ese estilo.
    s = sub(s, "// Check if translated text contains Cyrillic",
            "return; // español: se conserva el estilo en mayúsculas del juego\n#pragma warning disable CS0162")

    # --- construir SpanishValues después de cargar todo ---
    s = sub(s, "                Log.LogInfo(\"Loading passage dump for sequential fallback...\");",
            "                BuildSpanishValues();\n"
            "                Log.LogInfo(\"Loading passage dump for sequential fallback...\");")
    s = sub(s, "        void LoadDialogueTexts()",
            "        void BuildSpanishValues()\n"
            "        {\n"
            "            foreach (var v in Translations.Values) if (!string.IsNullOrEmpty(v)) SpanishValues.Add(v.Trim());\n"
            "            foreach (var v in KeyTranslations.Values) if (!string.IsNullOrEmpty(v)) SpanishValues.Add(v.Trim());\n"
            "            foreach (var lines in RussianPassages.Values)\n"
            "                foreach (var l in lines)\n"
            "                {\n"
            "                    if (string.IsNullOrEmpty(l) || l.StartsWith(\"$$\")) continue;\n"
            "                    SpanishValues.Add(l.Trim());\n"
            "                    int colon = l.IndexOf(\": \");\n"
            "                    if (colon > 0) SpanishValues.Add(l.Substring(colon + 2).Trim());\n"
            "                }\n"
            "            foreach (var chs in RussianChoices.Values)\n"
            "                foreach (var c in chs) if (c != null && c.Length > 0) SpanishValues.Add(c[0].Trim());\n"
            "            Log.LogInfo(string.Format(\"Spanish values (anti doble traducción): {0}\", SpanishValues.Count));\n"
            "        }\n\n"
            "        void LoadDialogueTexts()")

    # --- passages: primero el objeto exacto ---
    s = sub(s, 'RussianPassages.TryGetValue(objBase + ":" + passageTitle, out russianLines);',
            'RussianPassages.TryGetValue(objName + ":" + passageTitle, out russianLines);\n'
            '                        if (russianLines == null)\n'
            '                            RussianPassages.TryGetValue(objBase + ":" + passageTitle, out russianLines);')
    s = sub(s, 'RussianChoices.TryGetValue(objBase + ":" + passageTitle, out ruChoices);',
            'RussianChoices.TryGetValue(objName + ":" + passageTitle, out ruChoices);\n'
            '                                    if (ruChoices == null)\n'
            '                                        RussianChoices.TryGetValue(objBase + ":" + passageTitle, out ruChoices);')

    # --- fuentes: desactivadas por defecto ---
    s = sub(s, "private static ConfigEntry<float> FontScaleConfig;",
            "private static ConfigEntry<float> FontScaleConfig;\n"
            "        internal static bool FontReplacement = false;")
    s = sub(s, 'FontScaleConfig = Config.Bind("Font", "FontScale", 1.15f,',
            'FontReplacement = Config.Bind("Font", "EnableFontReplacement", false,\n'
            '                "Reemplazar fuentes del juego (solo si faltan glifos como ñ ¿ ¡)").Value;\n'
            '            FontScaleConfig = Config.Bind("Font", "FontScale", 1.0f,')
    s = sub(s, "                LoadCyrillicFonts();", "                if (FontReplacement) LoadCyrillicFonts();")

    # --- interruptores por capa (diagnóstico: activar/desactivar sin recompilar) ---
    s = sub(s, "        internal static bool FontReplacement = false;",
            "        internal static bool FontReplacement = false;\n"
            "        internal static bool LayerDialogs = true, LayerTextAssets = true, LayerTMP = true, LayerUIKeys = true;")
    s = sub(s, "            FontScale = FontScaleConfig.Value;",
            "            FontScale = FontScaleConfig.Value;\n"
            '            LayerDialogs = Config.Bind("Layers", "DialogObjects", true, "Reemplazar diálogos compilados (Spanish_Texts)").Value;\n'
            '            LayerTextAssets = Config.Bind("Layers", "TextAssets", true, "Reemplazar guiones TextAsset (intro, radio, periódicos...)").Value;\n'
            '            LayerTMP = Config.Bind("Layers", "TMPFallback", true, "Traducir textos TextMeshPro sueltos por mapping").Value;\n'
            '            LayerUIKeys = Config.Bind("Layers", "UIKeys", true, "Traducir claves de LocalizationManager").Value;\n'
            '            Log.LogInfo(string.Format("Capas: dialogs={0} textassets={1} tmp={2} uikeys={3}", LayerDialogs, LayerTextAssets, LayerTMP, LayerUIKeys));')
    s = sub(s, "                ReplaceDialogueObjects();", "                if (LayerDialogs) ReplaceDialogueObjects();")
    s = sub(s, "                ReplaceTextAssetContents();", "                if (LayerTextAssets) ReplaceTextAssetContents();")
    s = sub(s, "                PatchTMPText();", "                if (LayerTMP) PatchTMPText();")
    s = sub(s, "                PatchLocalizationManager(HarmonyInstance);", "                if (LayerUIKeys) PatchLocalizationManager(HarmonyInstance);")
    # --- refrescar LocalizedText ya dibujados (p. ej. la pantalla de aviso del inicio lee el
    #     texto antes de que se inyecten las traducciones y nunca lo vuelve a leer) ---
    s = sub(s, "                injectedByKey, injectedByValue, injectedByKey + injectedByValue, dict.Count, uninjected));\n            TranslationsInjected = true;",
            "                injectedByKey, injectedByValue, injectedByKey + injectedByValue, dict.Count, uninjected));\n"
            "            TranslationsInjected = true;\n"
            "            RefreshLocalizedTexts();")
    s = sub(s, "        void BuildSpanishValues()",
            "        static Type LocalizedTextType;\n"
            "        static void RefreshLocalizedTexts()\n"
            "        {\n"
            "            try\n"
            "            {\n"
            "                if (object.ReferenceEquals(LocalizedTextType, null))\n"
            "                    foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())\n"
            "                    {\n"
            "                        LocalizedTextType = asm.GetType(\"NC.I18N.LocalizedText\");\n"
            "                        if (!object.ReferenceEquals(LocalizedTextType, null)) break;\n"
            "                    }\n"
            "                if (object.ReferenceEquals(LocalizedTextType, null)) return;\n"
            "                MethodInfo update = LocalizedTextType.GetMethod(\"UpdateTextContent\", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);\n"
            "                if (object.ReferenceEquals(update, null)) return;\n"
            "                int n = 0;\n"
            "                foreach (var lt in Resources.FindObjectsOfTypeAll(LocalizedTextType))\n"
            "                {\n"
            "                    try { update.Invoke(lt, null); n++; } catch { }\n"
            "                }\n"
            "                Log.LogInfo(string.Format(\"LocalizedText refrescados: {0}\", n));\n"
            "            }\n"
            "            catch (Exception e) { Log.LogWarning(\"RefreshLocalizedTexts: \" + e.Message); }\n"
            "        }\n\n"
            "        void BuildSpanishValues()")

    # --- F5: recargar traducciones sin reiniciar el juego ---
    s = sub(s, "        private static Dictionary<string, string> TranslationsLower = null;",
            "        internal static Dictionary<string, string> TranslationsLower = null;")
    s = sub(s, "            // Scanner disabled - translation now happens in TMP_Text.text setter and LocalizationManager patch",
            "            // F5: recarga Spanish_UI/Spanish_Texts desde disco (usar tras tools/install.py).\n"
            "            // Los cambios se ven en las próximas líneas que muestre el juego.\n"
            "            if (Input.GetKeyDown(ReloadKey)) ReloadAll();")
    s = sub(s, "        void BuildSpanishValues()",
            "        void ReloadAll()\n"
            "        {\n"
            "            try\n"
            "            {\n"
            "                Translations.Clear(); KeyTranslations.Clear(); DialogueTexts.Clear();\n"
            "                RussianPassages.Clear(); RussianChoices.Clear(); GlobalLinkToChoiceTexts.Clear();\n"
            "                SpanishValues.Clear(); TranslationsLower = null; ReplacedDialogueIds.Clear();\n"
            "                LoadTranslations(); LoadDialogueTexts(); LoadKeyTranslations(); BuildSpanishValues();\n"
            "                if (LayerUIKeys && LocalizationPatched) TryInjectTranslations();\n"
            "                ReplaceTextAssetsInMemory();\n"
            "                processedTextKeys.Clear();\n"
            "                StartCoroutine(TranslateSceneDelayed());\n"
            "                Log.LogInfo(string.Format(\"[F5] Recargado: {0} textos, {1} claves, {2} passages\", Translations.Count, KeyTranslations.Count, RussianPassages.Count));\n"
            "            }\n"
            "            catch (Exception e) { Log.LogError(\"[F5] Error al recargar: \" + e); }\n"
            "        }\n\n"
            "        void BuildSpanishValues()")
    s = sub(s, "        internal static bool LayerDialogs = true, LayerTextAssets = true, LayerTMP = true, LayerUIKeys = true;",
            "        internal static bool LayerDialogs = true, LayerTextAssets = true, LayerTMP = true, LayerUIKeys = true;\n"
            "        internal static KeyCode ReloadKey = KeyCode.F5;")
    s = sub(s, '            LayerUIKeys = Config.Bind("Layers", "UIKeys", true, "Traducir claves de LocalizationManager").Value;',
            '            LayerUIKeys = Config.Bind("Layers", "UIKeys", true, "Traducir claves de LocalizationManager").Value;\n'
            '            ReloadKey = Config.Bind("Debug", "ReloadKey", KeyCode.F5, "Tecla para recargar traducciones").Value;')

    s = sub(s, "            string text;\n            if (DialogueTexts.TryGetValue(assetName, out text))",
            "            string text;\n            if (LayerTextAssets && DialogueTexts.TryGetValue(assetName, out text))")
    s = sub(s, "            EnumerateAndPatchAllFonts();", "            if (FontReplacement) EnumerateAndPatchAllFonts();")
    return s


if __name__ == "__main__":
    os.makedirs(os.path.join(DST, "Properties"), exist_ok=True)
    with open(os.path.join(SRC, "RussianLocalization.cs"), encoding="utf-8-sig") as f:
        cs = port_cs(f.read())
    with open(os.path.join(DST, "SpanishLocalization.cs"), "w", encoding="utf-8", newline="\n") as f:
        f.write(cs)
    with open(os.path.join(SRC, "NightCallRussian.csproj"), encoding="utf-8-sig") as f:
        proj = f.read()
    proj = proj.replace("NightCallRussian", "NightCallSpanish")
    proj = proj.replace(r"$(MSBuildThisFileDirectory)..\..\libs", r"$(MSBuildThisFileDirectory)..\..\ref-russian\libs")
    proj = proj.replace(r"$(MSBuildThisFileDirectory)..\..\data\BepInEx\core", r"$(MSBuildThisFileDirectory)..\..\ref-russian\data\BepInEx\core")
    proj = proj.replace("<GenerateAssemblyInfo>false</GenerateAssemblyInfo>",
                        "<GenerateAssemblyInfo>false</GenerateAssemblyInfo>\n    <NoWarn>CS0162</NoWarn>")
    with open(os.path.join(DST, "NightCallSpanish.csproj"), "w", encoding="utf-8", newline="\n") as f:
        f.write(proj)
    shutil.copy(os.path.join(SRC, "Properties", "AssemblyInfo.cs"), os.path.join(DST, "Properties", "AssemblyInfo.cs"))
    print("port listo: src/Mod/SpanishLocalization.cs")
