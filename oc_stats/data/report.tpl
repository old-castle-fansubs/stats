{%- import "comments.jinja" as comment_macros -%}
{%- import "requests.jinja" as request_macros -%}
{%- import "transmission.jinja" as transmission_macros -%}
{%- set max_comments = 5 -%}
{%- set max_requests = 9 -%}

<!DOCTYPE html>
<html lang='en'>
<head>
  <meta charset='utf-8'/>
  <title>Old Castle Fansubs - stats</title>
  <meta name='viewport' content='width=device-width, initial-scale=1, shrink-to-fit=no'>
  <link rel='stylesheet' type='text/css' href='https://bootswatch.com/4/minty/bootstrap.min.css'/>
  <style type='text/css'>{% include 'report-style.css' %}</style>
</head>
<body>
  <main class='container-fluid'>
    <section class='row justify-content-center'>
      <div class='col-lg-9 col-12'>
        <header class='page-header jumbotron pt-2 pb-2 mt-3 mb-3 text-center'>
          <h1>Old Castle Fansubs - statistics</h1>
          <p class='text-muted small'>Generated at {{ date.strftime('%Y-%m-%d %H:%M') }}</p>
        </header>
      </div>
    </section>

    <section class='row justify-content-center'>
      <div class='col-lg-9 col-12'>
        <ul class='nav nav-tabs' id='myTab' role='tablist'>
          <li class='nav-item'>
            <a class='nav-link active' id='dashboard-tab' data-toggle='tab' href='#dashboard' role='tab' aria-controls='dashboard' aria-selected='true'>Dashboard</a>
          </li>
          <li class='nav-item'>
            <a class='nav-link' id='comments-tab' data-toggle='tab' href='#comments' role='tab' aria-controls='comments' aria-selected='false'>Comments</a>
          </li>
          <li class='nav-item'>
            <a class='nav-link' id='requests-tab' data-toggle='tab' href='#requests' role='tab' aria-controls='requests' aria-selected='false'>Requests</a>
          </li>
        </ul>
        <div class='tab-content' id='myTabContent'>
          <div class='tab-pane fade show active' id='dashboard' role='tabpanel' aria-labelledby='dashboard-tab'>
            <div class='row justify-content-center'>
              <div class='col-xl-8 col-12'>
                <div class='daily-stats'>
                  <p class='float-right small mt-3 mb-0'>
                    {% if hits and downloads -%}
                      Total hits: {{ hits[-1].value }} {# -#}
                      Total downloads: {{ downloads[-1].value }}
                    {%- else -%}
                      Total hits: ? {# -#}
                      Total downloads: ?
                    {%- endif %}
                  </p>

                  <h2>Daily stats</h2>
                  <div class='target'></div>
                </div>

                <h2>Recent comments</h2>
                <p><small>Showing {{ comments[:max_comments]|length }} out of {{ comments|length }}</small></p>
                {{- comment_macros.render_comments(comments[:max_comments])|indent(14, True) }}
              </div>

              <div class='general col-xl-4 col-12'>
                <h2>Torrent stats</h2>
                {{- transmission_macros.render_torrents(torrents)|indent(14, True) }}

                <h2>Transmission</h2>
                {{- transmission_macros.render_torrent_stats(torrent_stats)|indent(14, True) }}

                <h2>Recent requests</h2>
                <p><small>Showing {{ anime_requests[:max_requests]|length }} out of {{ anime_requests|length }}</small></p>
                <ul class='requests-lite'>
                  {%- for request in anime_requests[:max_requests] %}
                    <li>
                      <a href='{{ request.link }}'>
                        {% if request.picture -%}
                          <img src='{{ request.picture }}' alt='{{ request.title }}'/>
                        {%- else -%}
                          <img src='img/unknown.jpg' alt='Unknown image'/>
                        {%- endif %}
                        <span>{{ request.title }}</span>
                      </a>
                    </li>
                  {%- endfor %}
                </ul>
              </div>
            </div>
          </div>

          <div class='tab-pane fade' id='comments' role='tabpanel' aria-labelledby='comments-tab'>
            <h2>All comments</h2>
            {{- comment_macros.render_comments(comments)|indent(10, True) }}
          </div>

          <div class='tab-pane fade' id='requests' role='tabpanel' aria-labelledby='requests-tab'>
            <h2>All requests</h2>
            {{- request_macros.render_requests(anime_requests)|indent(10, True) -}}
          </div>
        </div>
      </div>
    </section>
  </main>

  <script src='https://bootswatch.com/_vendor/jquery/dist/jquery.min.js'></script>
  <script src='https://bootswatch.com/_vendor/bootstrap/dist/js/bootstrap.min.js'></script>
  <script src='https://d3js.org/d3.v4.min.js'></script>
  <script>var hits = {{ hits|tojson|safe }};</script>
  <script>var downloads = {{ downloads|tojson|safe }};</script>
  <script>{% include 'report-daily-stats.js' %}</script>
</body>
</html>
