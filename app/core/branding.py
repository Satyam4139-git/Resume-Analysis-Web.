"""
Brand pages served by the backend (API docs, error pages).

They link to /theme.css, the same palette file the website uses, so the
backend and frontend always share one set of colors.
"""

from html import escape

_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#b5348a">
<title>{title} | CareerPilot AI</title>
<link rel="stylesheet" href="/theme.css">
<style>
  *{{box-sizing:border-box}}
  body{{margin:0;min-height:100vh;display:grid;place-items:center;padding:24px;
       font-family:var(--brand-font);color:#fff;background:var(--brand-gradient)}}
  main{{width:min(560px,100%);text-align:center}}
  .code{{font-size:clamp(72px,18vw,128px);font-weight:700;line-height:1;margin:0;
        text-shadow:0 6px 30px rgba(40,10,80,.35)}}
  h1{{font-size:clamp(22px,4vw,30px);margin:10px 0 8px}}
  p{{font-size:17px;opacity:.95;margin:0 0 28px}}
  a{{display:inline-block;background:#f2306f;color:#fff;text-decoration:none;font-weight:700;
     padding:14px 28px;border-radius:999px;box-shadow:0 10px 24px rgba(242,48,111,.45)}}
  a:hover{{filter:brightness(1.07)}}
</style>
</head>
<body>
<main>
  <p class="code">{code}</p>
  <h1>{heading}</h1>
  <p>{message}</p>
  <a href="/">Back to CareerPilot AI</a>
</main>
</body>
</html>"""

_MESSAGES = {
    404: ("Page not found", "The page you are looking for does not exist or has moved."),
    405: ("Not allowed", "That action is not supported here."),
    500: ("Something went wrong", "We hit an unexpected problem. Please try again in a moment."),
    503: ("Temporarily unavailable", "This feature is not available right now. Please try again later."),
}


def error_page(status_code: int, detail: str = "") -> str:
    heading, message = _MESSAGES.get(
        status_code, ("Something went wrong", "Please go back and try again.")
    )
    if detail and status_code not in (404, 500):
        message = detail
    return _PAGE.format(
        title=escape(heading),
        code=status_code,
        heading=escape(heading),
        message=escape(message),
    )


DOCS_CSS = """
<link rel="stylesheet" href="/theme.css">
<style>
  body{margin:0}
  .swagger-ui .topbar{background:var(--brand-gradient);padding:14px 0}
  .swagger-ui .info .title{color:var(--brand-purple);font-family:var(--brand-font)}
  .swagger-ui .btn.execute{background:var(--brand-pink-deep);border-color:var(--brand-pink-deep)}
  .swagger-ui .btn.authorize{color:var(--brand-pink-deep);border-color:var(--brand-pink-deep)}
  .swagger-ui .opblock.opblock-get .opblock-summary-method{background:var(--brand-indigo)}
  .swagger-ui .opblock.opblock-post .opblock-summary-method{background:var(--brand-pink-deep)}
  .swagger-ui .opblock-tag{font-family:var(--brand-font)}
  body:before{content:"CareerPilot AI  ·  API";display:block;color:#fff;font:700 20px var(--brand-font);
    padding:16px 24px;background:var(--brand-gradient)}
</style>
"""
