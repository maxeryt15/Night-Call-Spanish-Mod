using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using BepInEx;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace NightCallSpanish.Dumper
{
    // Vuelca el texto original del juego (diálogos Prompter, localización UI y TextAssets)
    // a <juego>/NightCallDumper_out/. Se ejecuta en cada carga de escena y con F9.
    [BepInPlugin("com.nightcall.spanish.dumper", "Night Call Source Dumper", "0.1.0")]
    public class NightCallDumper : BaseUnityPlugin
    {
        const BindingFlags BF = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance;

        string _out;
        readonly HashSet<string> _dumpedDialogs = new HashSet<string>();
        readonly HashSet<string> _dumpedAssets = new HashSet<string>();
        readonly HashSet<string> _dumpedLoc = new HashSet<string>();

        void Awake()
        {
            _out = Path.Combine(Path.GetDirectoryName(Application.dataPath), "NightCallDumper_out");
            Directory.CreateDirectory(_out);
            SceneManager.sceneLoaded += (s, m) => StartCoroutine(DumpLater(s.name));
            Logger.LogInfo("Dumper listo. Salida: " + _out + " (F9 para volcar de nuevo)");
        }

        void Update()
        {
            if (Input.GetKeyDown(KeyCode.F9)) DumpAll("F9");
        }

        IEnumerator DumpLater(string scene)
        {
            yield return new WaitForSeconds(2f);
            DumpAll(scene);
        }

        void DumpAll(string reason)
        {
            int d = 0, l = 0, t = 0;
            try { d = DumpDialogs(); } catch (Exception e) { Logger.LogError("Dialogs: " + e); }
            try { l = DumpLocalization(); } catch (Exception e) { Logger.LogError("Localization: " + e); }
            try { t = DumpTextAssets(); } catch (Exception e) { Logger.LogError("TextAssets: " + e); }
            try { DumpReveals(); } catch (Exception e) { Logger.LogError("Reveals: " + e); }
            Logger.LogInfo(string.Format("[{0}] nuevos: dialogos={1} idiomas UI={2} textassets={3} | totales: {4}/{5}/{6}",
                reason, d, l, t, _dumpedDialogs.Count, _dumpedLoc.Count, _dumpedAssets.Count));
        }

        static Type FindType(string fullName)
        {
            foreach (var a in AppDomain.CurrentDomain.GetAssemblies())
            {
                Type t = null;
                try { t = a.GetType(fullName, false); } catch { }
                if (!ReferenceEquals(t, null)) return t;
            }
            return null;
        }

        static object Get(object o, string field)
        {
            if (o == null) return null;
            var f = o.GetType().GetField(field, BF);
            return ReferenceEquals(f, null) ? null : f.GetValue(o);
        }

        // ---------- Diálogos ----------
        int DumpDialogs()
        {
            var type = FindType("NC.Dialogs.DialogObjectScript");
            if (ReferenceEquals(type, null)) return 0;
            int n = 0;
            foreach (var obj in Resources.FindObjectsOfTypeAll(type))
            {
                if (obj == null || string.IsNullOrEmpty(obj.name)) continue;
                var list = Get(obj, "dialogs") as IList;
                if (list == null) continue;
                foreach (var i18n in list)
                {
                    if (i18n == null) continue;
                    string lang = Convert.ToString(Get(i18n, "lang"));
                    var dialog = Get(i18n, "dialog");
                    if (dialog == null) continue;
                    string key = lang + "/" + obj.name;
                    if (_dumpedDialogs.Contains(key)) continue;

                    var passages = Get(dialog, "_passages") as IList;
                    if (passages == null || passages.Count == 0) continue;

                    var sb = new StringBuilder();
                    sb.Append("{\"object\":").Append(J(obj.name))
                      .Append(",\"title\":").Append(J(Convert.ToString(Get(obj, "title"))))
                      .Append(",\"lang\":").Append(J(lang))
                      .Append(",\"passages\":[\n");
                    for (int p = 0; p < passages.Count; p++)
                    {
                        var ps = passages[p];
                        if (p > 0) sb.Append(",\n");
                        sb.Append("{\"title\":").Append(J(Convert.ToString(Get(ps, "_title"))))
                          .Append(",\"link\":").Append(J(Convert.ToString(Get(ps, "_link"))))
                          .Append(",\"lines\":[");
                        var lines = Get(ps, "_lines") as IList;
                        if (lines != null)
                            for (int i = 0; i < lines.Count; i++)
                                sb.Append(i > 0 ? "," : "").Append(J(Convert.ToString(lines[i])));
                        sb.Append("],\"choices\":[");
                        var choices = Get(ps, "_choices") as IList;
                        if (choices != null)
                            for (int i = 0; i < choices.Count; i++)
                                sb.Append(i > 0 ? "," : "")
                                  .Append("{\"text\":").Append(J(Convert.ToString(Get(choices[i], "_text"))))
                                  .Append(",\"link\":").Append(J(Convert.ToString(Get(choices[i], "_link"))))
                                  .Append(",\"ending\":").Append(Convert.ToBoolean(Get(choices[i], "_ending")) ? "true" : "false")
                                  .Append("}");
                        sb.Append("]}");
                    }
                    sb.Append("\n]}\n");

                    string dir = Path.Combine(Path.Combine(_out, "dialogs"), lang);
                    Directory.CreateDirectory(dir);
                    File.WriteAllText(Path.Combine(dir, Safe(obj.name) + ".json"), sb.ToString(), new UTF8Encoding(false));
                    _dumpedDialogs.Add(key);
                    n++;
                }
            }
            return n;
        }

        // ---------- Localización UI (clave -> texto) ----------
        int DumpLocalization()
        {
            var datas = new List<object>();
            var ldType = FindType("NC.I18N.LocalizationData");
            if (!ReferenceEquals(ldType, null) && typeof(UnityEngine.Object).IsAssignableFrom(ldType))
                datas.AddRange(Resources.FindObjectsOfTypeAll(ldType).Cast<object>());
            var lmType = FindType("NC.I18N.LocalizationManager");
            if (!ReferenceEquals(lmType, null) && typeof(UnityEngine.Object).IsAssignableFrom(lmType))
                foreach (var lm in Resources.FindObjectsOfTypeAll(lmType))
                {
                    var holder = Get(lm, "_lang_holder");
                    var lst = Get(holder, "_localization_datas") as IList;
                    if (lst != null) foreach (var x in lst) if (x != null) datas.Add(x);
                }

            int n = 0;
            foreach (var data in datas)
            {
                string lang = Convert.ToString(Get(data, "_lang"));
                var items = Get(data, "_items") as IList;
                if (items == null || items.Count == 0 || _dumpedLoc.Contains(lang)) continue;
                var sb = new StringBuilder("{\n");
                bool first = true;
                foreach (var it in items)
                {
                    if (it == null) continue;
                    sb.Append(first ? "" : ",\n").Append(J(Convert.ToString(Get(it, "_key"))))
                      .Append(": ").Append(J(Convert.ToString(Get(it, "_value"))));
                    first = false;
                }
                sb.Append("\n}\n");
                File.WriteAllText(Path.Combine(_out, "localization_" + lang + ".json"), sb.ToString(), new UTF8Encoding(false));
                _dumpedLoc.Add(lang);
                n++;
            }
            return n;
        }

        // ---------- TextAssets ----------
        // ---------- Passidex: reveals (descripciones de cada pasajero) ----------
        bool _dumpedReveals;

        void DumpReveals()
        {
            if (_dumpedReveals) return;
            var type = FindType("NC.Passengers.RevealScript");
            if (ReferenceEquals(type, null)) return;
            var sb = new StringBuilder("[\n");
            int n = 0;
            foreach (var script in Resources.FindObjectsOfTypeAll(type))
            {
                var reveals = Get(script, "reveals") as IList;
                if (reveals == null) continue;
                foreach (var r in reveals)
                {
                    if (r == null) continue;
                    sb.Append(n++ > 0 ? ",\n" : "")
                      .Append("{\"script\":").Append(J(script.name))
                      .Append(",\"passenger\":").Append(J(Convert.ToString(Get(r, "passenger_name"))))
                      .Append(",\"passenger_id\":").Append(Convert.ToString(Get(r, "passenger_id")))
                      .Append(",\"reveal_id\":").Append(J(Convert.ToString(Get(r, "reveal_id"))))
                      .Append(",\"title\":").Append(JList(Get(r, "title") as IList))
                      .Append(",\"text\":").Append(JList(Get(r, "text") as IList))
                      .Append("}");
                }
            }
            if (n == 0) return;
            sb.Append("\n]\n");
            File.WriteAllText(Path.Combine(_out, "reveals.json"), sb.ToString(), new UTF8Encoding(false));
            _dumpedReveals = true;
            Logger.LogInfo("Reveals volcadas: " + n);
        }

        static string JList(IList list)
        {
            if (list == null) return "[]";
            var sb = new StringBuilder("[");
            for (int i = 0; i < list.Count; i++)
                sb.Append(i > 0 ? "," : "").Append(J(Convert.ToString(list[i])));
            return sb.Append("]").ToString();
        }

        int DumpTextAssets()
        {
            string dir = Path.Combine(_out, "textassets");
            Directory.CreateDirectory(dir);
            int n = 0;
            foreach (var ta in Resources.FindObjectsOfTypeAll<TextAsset>())
            {
                if (ta == null || string.IsNullOrEmpty(ta.name) || _dumpedAssets.Contains(ta.name)) continue;
                File.WriteAllBytes(Path.Combine(dir, Safe(ta.name) + ".txt"), ta.bytes);
                _dumpedAssets.Add(ta.name);
                n++;
            }
            return n;
        }

        static string Safe(string s)
        {
            foreach (char c in Path.GetInvalidFileNameChars()) s = s.Replace(c, '_');
            return s;
        }

        static string J(string s)
        {
            if (s == null) return "null";
            var sb = new StringBuilder("\"");
            foreach (char c in s)
            {
                switch (c)
                {
                    case '"': sb.Append("\\\""); break;
                    case '\\': sb.Append("\\\\"); break;
                    case '\n': sb.Append("\\n"); break;
                    case '\r': sb.Append("\\r"); break;
                    case '\t': sb.Append("\\t"); break;
                    default:
                        if (c < 0x20) sb.Append("\\u").Append(((int)c).ToString("x4"));
                        else sb.Append(c);
                        break;
                }
            }
            return sb.Append('"').ToString();
        }
    }
}
