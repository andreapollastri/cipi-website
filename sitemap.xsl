<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:sm="http://www.sitemaps.org/schemas/sitemap/0.9"
  xmlns:xhtml="http://www.w3.org/1999/xhtml"
  exclude-result-prefixes="sm xhtml">
  <xsl:output method="html" encoding="UTF-8" indent="yes"/>
  <xsl:template match="/">
    <html lang="en">
      <head>
        <meta charset="UTF-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <title>Cipi sitemap</title>
        <style>
          :root { color-scheme: light; }
          body { font: 15px/1.45 ui-sans-serif, system-ui, sans-serif; margin: 2rem; color: #111; background: #fafafa; }
          h1 { font-size: 1.35rem; margin: 0 0 .25rem; }
          p { color: #555; margin: 0 0 1.25rem; }
          table { border-collapse: collapse; width: 100%; max-width: 1100px; background: #fff; }
          th, td { text-align: left; padding: .55rem .7rem; border-bottom: 1px solid #e5e5e5; vertical-align: top; }
          th { font-size: .75rem; text-transform: uppercase; letter-spacing: .04em; color: #666; }
          tr.home td { background: #ecfccb; font-weight: 600; }
          a { color: #3f6212; word-break: break-all; }
          .pri { font-variant-numeric: tabular-nums; }
          .meta { white-space: nowrap; color: #666; font-size: .9rem; }
        </style>
      </head>
      <body>
        <h1>Cipi — XML sitemap</h1>
        <p>
          <xsl:value-of select="count(sm:urlset/sm:url)"/>
          URLs · homepage entries highlighted ·
          <a href="https://cipi.sh/">cipi.sh</a>
        </p>
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>URL</th>
              <th>Priority</th>
              <th>Changefreq</th>
              <th>Lastmod</th>
            </tr>
          </thead>
          <tbody>
            <xsl:for-each select="sm:urlset/sm:url">
              <tr>
                <xsl:if test="sm:loc='https://cipi.sh/' or sm:loc='https://cipi.sh/it/' or sm:loc='https://cipi.sh/'">
                  <xsl:attribute name="class">home</xsl:attribute>
                </xsl:if>
                <td class="meta"><xsl:value-of select="position()"/></td>
                <td><a href="{sm:loc}"><xsl:value-of select="sm:loc"/></a></td>
                <td class="pri"><xsl:value-of select="sm:priority"/></td>
                <td class="meta"><xsl:value-of select="sm:changefreq"/></td>
                <td class="meta"><xsl:value-of select="sm:lastmod"/></td>
              </tr>
            </xsl:for-each>
          </tbody>
        </table>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
