"""Knowledge base: markdown-as-graph (spec §15).

Files are nodes, [[wikilinks]] in '## Relations' are typed edges, YAML
frontmatter holds node properties. Git is the source of truth; `kb index`
derives _index.md files and graph.json from the files.
"""
