import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.text.MessageFormat;
import java.util.*;
import java.util.jar.*;
import java.util.regex.*;
import javax.xml.parsers.DocumentBuilderFactory;

public class ValidatePack {
  static Properties load(InputStream input) throws Exception {
    Properties p = new Properties();
    try (var reader = new InputStreamReader(input, StandardCharsets.UTF_8)) { p.load(reader); }
    return p;
  }
  public static void main(String[] args) throws Exception {
    Path ide = Path.of(args[0]);
    Path plugin = Path.of(args[1]);
    var sources = new HashMap<String, Properties>();
    try (var paths = Files.walk(ide)) {
      for (Path path : paths.filter(p -> p.toString().endsWith(".jar") && !p.toString().contains("/localization-")).toList()) {
        try (JarFile jar = new JarFile(path.toFile())) {
          for (var entry : Collections.list(jar.entries())) {
            String n = entry.getName();
            if (!n.matches("messages/[^/]+\\.properties") || n.matches(".*_(fr|en|ja|ko|zh)(_[A-Z]+)?\\.properties")) continue;
            Properties p = load(jar.getInputStream(entry));
            sources.computeIfAbsent(n, k -> new Properties()).putAll(p);
          }
        }
      }
    }
    int bundles = 0, entries = 0, formats = 0;
    var formatErrors = new ArrayList<String>();
    var repairKeys = new ArrayList<String>();
    try (JarFile jar = new JarFile(plugin.toFile())) {
      var factory = DocumentBuilderFactory.newInstance();
      factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
      var descriptor = factory.newDocumentBuilder().parse(jar.getInputStream(jar.getJarEntry("META-INF/plugin.xml")));
      if (!descriptor.getElementsByTagName("languageBundle").item(0).getAttributes().getNamedItem("locale").getNodeValue().equals("fr")) throw new AssertionError("locale");
      for (var source : sources.entrySet()) {
        var entry = jar.getJarEntry(source.getKey());
        if (entry == null) throw new AssertionError("Missing bundle " + source.getKey());
        Properties translated = load(jar.getInputStream(entry));
        if (!translated.stringPropertyNames().equals(source.getValue().stringPropertyNames())) throw new AssertionError("Different keys " + source.getKey());
        bundles++;
        for (String key : translated.stringPropertyNames()) {
          entries++;
          String original = source.getValue().getProperty(key), french = translated.getProperty(key);
          // Check only strings for which the source itself is a Java MessageFormat pattern.
          if (!original.matches("(?s).*\\{[0-9]+.*")) continue;
          MessageFormat before;
          try { before = new MessageFormat(original, Locale.ENGLISH); } catch (IllegalArgumentException ex) { continue; }
          try {
            var after = new MessageFormat(french, Locale.FRENCH);
            if (before.getFormatsByArgumentIndex().length != after.getFormatsByArgumentIndex().length) {
              formatErrors.add(source.getKey() + ":" + key + " argument count changed");
              repairKeys.add(source.getKey() + "\t" + key);
            }
            formats++;
          } catch (IllegalArgumentException ex) {
            formatErrors.add(source.getKey() + ":" + key + " " + ex.getMessage());
            repairKeys.add(source.getKey() + "\t" + key);
          }
        }
      }
      Properties common = load(jar.getInputStream(jar.getJarEntry("messages/CommonBundle.properties")));
      if (!common.getProperty("button.cancel").equals("Annuler")) throw new AssertionError("French Cancel");
      if (!common.getProperty("title.settings").equals("Paramètres")) throw new AssertionError("French Settings");
    }
    System.out.printf("bundles=%d entries=%d messageFormats=%d errors=%d%n", bundles, entries, formats, formatErrors.size());
    for (String error : formatErrors) System.out.println(error);
    if (args.length > 2 && !repairKeys.isEmpty()) Files.write(Path.of(args[2]), repairKeys, StandardCharsets.UTF_8);
    if (!formatErrors.isEmpty()) System.exit(1);
  }
}
