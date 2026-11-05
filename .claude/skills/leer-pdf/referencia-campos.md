# Referencia: detección de campos en documentos guatemaltecos

Todas las expresiones asumen texto normalizado (NFC, espacios colapsados) y `re.IGNORECASE`.
Los resultados son **sugerencias** con confianza; el usuario confirma.

## Factura electrónica (FEL / DTE)

| Campo | Patrón orientativo |
|---|---|
| Número de autorización (UUID) | `\b[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}\b` |
| Serie | `serie[:\s]+([0-9A-F]{8})` |
| Número DTE | `(?:n[úu]mero(?:\s+de)?\s+dte|no\.?\s*dte)[:\s]+(\d{6,10})` |
| NIT | `nit[:\s]*([0-9]{1,12}-?[0-9Kk])` → validar dígito verificador |
| "Consumidor Final" | `\bC/?F\b|consumidor\s+final` → NIT = `CF` |
| Fecha | `(\d{2})[/-](\d{2})[/-](\d{4})` (formato dd/mm/aaaa) |
| Total | `total[^\d]{0,20}Q?\s*([\d,]+\.\d{2})` |
| IVA | `iva[^\d]{0,20}Q?\s*([\d,]+\.\d{2})` |

Coherencia a verificar tras extraer: `total ≈ suma de líneas`; si precios incluyen IVA, `iva ≈ total / 1.12 * 0.12` (tolerancia ±0.02).

### Validación de NIT (módulo 11)

```python
def nit_valido(nit: str) -> bool:
    nit = nit.upper().replace("-", "").replace(" ", "")
    if nit == "CF":
        return True
    if len(nit) < 2 or not nit[:-1].isdigit():
        return False
    cuerpo, verificador = nit[:-1], nit[-1]
    suma = sum(int(d) * p for d, p in zip(cuerpo, range(len(cuerpo) + 1, 1, -1)))
    esperado = (11 - suma % 11) % 11
    return verificador == ("K" if esperado == 10 else str(esperado))
```

## Contratos

| Campo | Pista |
|---|---|
| Tipo | palabras clave: `compraventa`, `arrendamiento`, `promesa de compraventa`, `usufructo`, `servicios` |
| DPI / CUI | `\b\d{4}\s?\d{5}\s?\d{4}\b` (13 dígitos) |
| Partes | frases `comparece(n)`, `en calidad de`, `vendedor(a)`, `comprador(a)`, `arrendante`, `arrendatario` |
| Fecha en letras | "a los quince días del mes de marzo de dos mil veinticinco" → requiere conversor de números en letras |
| Monto | `(?:Q|quetzales)\s*([\d,]+\.\d{2})` y su versión en letras |
| Registro | ver sección de planos (finca/folio/libro) |

## Planos y datos registrales

| Campo | Patrón orientativo |
|---|---|
| Finca | `finca\s*(?:n[úu]mero|no\.?)?\s*([\d,]+)` |
| Folio | `folio\s*(?:n[úu]mero|no\.?)?\s*([\d,]+)` |
| Libro | `libro\s*(?:n[úu]mero|no\.?)?\s*([\d,]+)(?:\s*(?:de|E)\s*([A-Za-zñÑ ]+))?` |
| Área | `([\d,]+(?:\.\d+)?)\s*(m2|m²|mts2|metros cuadrados|v2|varas cuadradas|mz|manzanas)` |
| Escala | `escala\s*1\s*:\s*(\d+)` |
| Colegiado | `colegiado\s*(?:no\.?)?\s*(\d+)` |

Conversiones de área (guardar siempre en m²):
- 1 vara² = 0.698896 m²
- 1 manzana = 10 000 varas² = 6 988.96 m²
- 1 hectárea = 10 000 m²

Coordenadas en planos guatemaltecos suelen venir en **GTM** (Guatemala Transversa de Mercator) o UTM zona 15/16 N — guardar el sistema de referencia junto a las coordenadas.
