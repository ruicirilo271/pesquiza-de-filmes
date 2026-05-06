from flask import Flask, render_template, request
import requests
from urllib.parse import quote_plus

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    error = None
    query = ""

    if request.method == "POST":
        query = request.form.get("query", "").strip()

        if not query:
            error = "Escreve o nome de um filme."
        else:
            encoded_query = quote_plus(query)

            # ✅ Endpoint fixo
            url = f"https://movies-api.accel.li/api/v2/list_movies.json?query_term={encoded_query}&limit=20"

            headers = {
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/123.0 Safari/537.36"
                ),
                "Referer": "[movies-api.accel.li](https://movies-api.accel.li/)",
                "Origin": "[movies-api.accel.li](https://movies-api.accel.li)"
            }

            try:
                print("URL final:", url)
                response = requests.get(url, headers=headers, timeout=15)
                content_type = response.headers.get("Content-Type", "")

                if "application/json" not in content_type:
                    print("Conteúdo inesperado:", response.text[:400])
                    raise ValueError("A resposta da API não veio em formato JSON válido.")

                data = response.json()

                if data.get("status") != "ok":
                    error = data.get("status_message", "Erro na API.")
                else:
                    movies = data.get("data", {}).get("movies", [])
                    if not movies:
                        error = "Nenhum filme encontrado."
                    else:
                        for movie in movies:
                            torrents = [
                                {
                                    "quality": t.get("quality"),
                                    "size": t.get("size"),
                                    # link direto (pode estar bloqueado)
                                    "url": t.get("url"),
                                    # magnet gerado localmente
                                    "magnet": f"magnet:?xt=urn:btih:{t.get('hash')}&dn={quote_plus(movie.get('title',''))}"
                                }
                                for t in movie.get("torrents", [])
                            ]

                            results.append({
                                "title": movie.get("title", "Sem título"),
                                "year": movie.get("year", ""),
                                "rating": movie.get("rating", ""),
                                "runtime": movie.get("runtime", ""),
                                "genres": movie.get("genres", []),
                                "summary": (
                                    movie.get("summary")
                                    or movie.get("description_full")
                                    or "Sem sinopse"
                                ),
                                "img": movie.get("medium_cover_image", ""),
                                "trailer": movie.get("yt_trailer_code", ""),
                                "url": movie.get("url", ""),
                                "torrents": torrents
                            })

            except ValueError as e:
                error = str(e)
            except requests.exceptions.Timeout:
                error = "A API demorou demasiado tempo a responder."
            except requests.exceptions.ConnectionError:
                error = "Não foi possível ligar à API."
            except requests.exceptions.RequestException as e:
                error = f"Erro HTTP: {e}"
            except Exception as e:
                error = f"Erro inesperado: {e}"

    return render_template("index.html", results=results, error=error, query=query)


if __name__ == "__main__":
    app.run(debug=True)

