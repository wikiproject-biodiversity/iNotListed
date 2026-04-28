[English](README.md) · [Français](README.fr.md) · **Español** · [日本語](README.ja.md) · [മലയാളം](README.ml.md) · [Igbo](README.ig.md) · [Dagbanli](README.dag.md)

# iNotWiki — artículos de Wikipedia faltantes

> 🌍 *Esta traducción al español fue generada con ayuda de una IA.
> Se agradecen las contribuciones y revisiones de la comunidad —
> [abre un *issue* en Codeberg](https://codeberg.org/wikiproject-biodiversity/iNotListed/issues)
> o edita este archivo directamente.*

Herramienta de línea de comandos para encontrar **artículos de Wikipedia
faltantes** sobre taxones biológicos, usando **iNaturalist** y **Wikidata**.

> **Alojamiento redundante.** Este proyecto se publica intencionadamente en
> dos forjas independientes para seguir disponible si alguna deja de funcionar
> o cambia sus condiciones:
>
> - **Principal:** [codeberg.org/wikiproject-biodiversity/iNotListed](https://codeberg.org/wikiproject-biodiversity/iNotListed) — *issues*, PR y CI.
> - **Espejo:** [github.com/wikiproject-biodiversity/iNotListed](https://github.com/wikiproject-biodiversity/iNotListed) — sincronizado, solo lectura.

## Características
- Obtiene observaciones de **iNaturalist** con paginación mediante `id_above`
  (funciona para más de 10 000 observaciones).
- Consulta **Wikidata** y comprueba si cada taxón tiene artículo en
  Wikipedia para los idiomas solicitados.
- Genera un informe Markdown con una tabla por taxón y gráficos PNG con
  las especies más observadas y los observadores más activos.
- Se identifica como `iNotListed/<versión>` y reintenta las respuestas HTTP
  transitorias (429 / 5xx) con *backoff* exponencial.

---

## Instalación
Requiere **Python 3.9+**.

```sh
pip install requests matplotlib
```

---

## Uso
```sh
python iNotWiki.py [opciones]
```

Indique exactamente **uno** de `--project_id`, `--username` o `--country_id`.
Si no se indica ninguno, se usa el proyecto `biohackathon-2025`.

| Opción            | Descripción                                                       |
|-------------------|-------------------------------------------------------------------|
| `--project_id`    | ID o *slug* de un proyecto en iNaturalist (p. ej. `biohackathon-2025`) |
| `--username`      | Nombre de usuario en iNaturalist                                  |
| `--country_id`    | ID de lugar en iNaturalist                                        |
| `--languages`     | Códigos de idioma de Wikipedia separados por coma (por defecto: `en,es,ja,ar,nl,pt,fr`) |
| `--output-folder` | Carpeta para el informe Markdown y los PNG (por defecto: `reports`) |

El script imprime la ruta del informe Markdown en stdout, para capturarla
fácilmente en *shell*:

```sh
REPORT_PATH=$(python iNotWiki.py --project_id biohackathon-2025)
```

En Forgejo Actions también escribe `report_path=…` en `$GITHUB_OUTPUT`.

---

## Ejemplos

```sh
# Proyecto (slug o ID numérico)
python iNotWiki.py --project_id biohackathon-2025

# Usuario, restringido a unos pocos idiomas
python iNotWiki.py --username johndoe --languages en,nl,de

# Lugar / país
python iNotWiki.py --country_id 7088 --output-folder reports/colombia
```

---

## Interfaz por *issues* (Codeberg / Forgejo Actions)
Dos plantillas de *issue* lanzan los *workflows* en `.forgejo/workflows/`:

- **`[Wikiblitz]: …`** — ejecuta el *workflow* solo de proyecto.
- **`[Missing Wikipedia]: …`** — formulario completo (proyecto / usuario /
  país + casillas de idiomas).

Ambos *workflows* guardan el informe en `reports/issue-<n>/` y publican
(una versión truncada del) Markdown como comentario del *issue*.

---

## Desarrollo
Por ahora la herramienta vive en un único archivo (`iNotWiki.py`).
Hay un pequeño bot de Telegram en desarrollo — véase el rastreador
de *issues*.

## Licencia
MIT.
