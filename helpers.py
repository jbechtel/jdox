
def format_response(response):
    r = response.response
    r += "\n\nReferences\n"
    # urls = set(x.metadata['URL'] for x in response.source_nodes)
    seen = []

    for i, source in enumerate(response.source_nodes):
        if source.metadata['URL'] not in seen:
            # r += f"""\n {i + 1}. "{source.metadata['file_name']}". Page {source.metadata['page_label']}"""
            r += f"""\n {len(seen) + 1}.  {source.metadata['URL']}"""
        seen.append(source.metadata['URL'])

    # for i, source in enumerate(response.source_nodes):
    #     # r += f"""\n {i + 1}. "{source.metadata['file_name']}". Page {source.metadata['page_label']}"""
    #     r += f"""\n {i + 1}.  {source.metadata['URL']}"""

    return r
