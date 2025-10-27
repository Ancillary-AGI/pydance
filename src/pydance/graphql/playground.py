"""
GraphQL Playground for Pydance framework.
"""

from typing import Dict, Any, Optional


class GraphQLPlayground:
    """GraphQL Playground for development and testing"""

    def __init__(self, endpoint: str = "/graphql"):
        self.endpoint = endpoint

    def get_html(self) -> str:
        """Get GraphQL Playground HTML"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>GraphQL Playground</title>
            <link rel="stylesheet" href="//cdn.jsdelivr.net/npm/graphql-playground-react/build/static/css/index.css" />
            <link rel="shortcut icon" href="//cdn.jsdelivr.net/npm/graphql-playground-react/build/favicon.png" />
            <script src="//cdn.jsdelivr.net/npm/graphql-playground-react/build/static/js/middleware.js"></script>
        </head>
        <body>
            <div id="root">
                <style>
                    body {{
                        background-color: rgb(23, 42, 58);
                        font-family: Open Sans, sans-serif;
                        height: 90vh;
                    }}
                    #root {{
                        height: 100%;
                        width: 100%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }}
                    .loading {{
                        font-size: 32px;
                        font-weight: 200;
                        color: rgba(255, 255, 255, .6);
                        margin-left: 20px;
                    }}
                    img.info {{
                        float: left;
                        margin-right: 10px;
                    }}
                </style>
                <img src="//cdn.jsdelivr.net/npm/graphql-playground-react/build/logo.png" alt="" class="info" />
                <div class="loading">Loading...</div>
            </div>
            <script>
                window.addEventListener('load', function (event) {{
                    GraphQLPlayground.init(document.getElementById('root'), {{
                        endpoint: '{endpoint}'
                    }})
                }})
            </script>
        </body>
        </html>
        """.format(endpoint=self.endpoint)

        return html


__all__ = ['GraphQLPlayground']
