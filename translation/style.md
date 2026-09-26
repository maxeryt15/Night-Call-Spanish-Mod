# Guía de estilo — Night Call en español

## Registro
- **Tú** en todo el juego (taxista ↔ pasajeros, pasajeros entre sí, policía incluida salvo que el original marque formalidad explícita, p. ej. "Monsieur", "Sir").
- **Ustedes** para el plural. Nunca "vosotros".
- Español neutro: evitar regionalismos marcados ("coger", "vale", "che", "guay", "ahorita"). Términos fijos en el glosario (`translation/glossary.json`).

## Comillas y puntuación
- **Mantener exactamente las comillas del original** de cada línea: si el inglés usa “ ”, el español usa “ ”; si usa « », el español usa « ». El validador lo controla.
- Signos de apertura obligatorios: ¿ ¡.
- Puntos suspensivos: mantener el carácter del original (… o ...).
- No agregar comillas a líneas de narración que no las tienen.

## Lo que nunca se toca
- Nombres de hablante al inicio de la línea (`PATRICIA:`) — el extractor ya los separa; se traduce solo el cuerpo.
- Emotes (`:smile:`, `:silence:`), comandos `$$ … $$`, `{variables}`, links `->`, etiquetas `<…>`.

## Choices
- Cortas y naturales. Acciones entre paréntesis en infinitivo: "(Say nothing.)" → "(No decir nada.)", "(Wait.)" → "(Esperar.)".

## Nombres propios
- Personajes y lugares de París se mantienen en su forma original (Hervé, Jérôme, Bois-de-Vincennes).
