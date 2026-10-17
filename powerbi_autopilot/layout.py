from __future__ import annotations


def grid_to_pixels(items: list[dict], width: int = 1920, height: int = 1080, columns: int = 12, margin: int = 32, gap: int = 16, top: int = 96, row_height: int = 160) -> dict:
    """Converte posições (coluna e linha de base 1) em retângulos; não produz PBIR."""
    if columns < 1 or min(width, height) <= 0 or gap < 0 or margin < 0 or row_height <= 0:
        raise ValueError('Parâmetros de grid inválidos')
    content_width = width - 2 * margin
    col_width = (content_width - gap * (columns - 1)) / columns
    if col_width <= 0:
        raise ValueError('Não há espaço para a grade no canvas')
    result = []
    for item in items:
        col, row, span = item['column'], item['row'], item['span']
        rowspan = item.get('row_span', 1)
        if min(col, row, span, rowspan) < 1 or col + span - 1 > columns:
            raise ValueError(f'Item fora da grade: {item["id"]}')
        rect = {'id': item['id'], 'x': round(margin + (col-1)*(col_width+gap),2), 'y': top + (row-1)*(row_height+gap), 'width': round(span*col_width+(span-1)*gap,2), 'height': rowspan*row_height+(rowspan-1)*gap}
        if rect['y'] + rect['height'] > height:
            raise ValueError(f'Item ultrapassa altura da página: {item["id"]}')
        for prev in result:
            if rect['x'] < prev['x']+prev['width']-0.001 and rect['x']+rect['width'] > prev['x']+0.001 and rect['y'] < prev['y']+prev['height']-0.001 and rect['y']+rect['height'] > prev['y']+0.001:
                raise ValueError(f'Sobreposição entre {item["id"]} e {prev["id"]}')
        result.append(rect)
    return {'canvas':{'width':width,'height':height}, 'grid':{'columns':columns,'gap':gap,'margin':margin,'row_height':row_height}, 'placements': result}


def draft_layout(plan: dict) -> dict:
    # Standard first-page skeleton; not yet chart-specific adaptive design.
    return grid_to_pixels([
        {'id':'kpi_1','column':1,'row':1,'span':3},
        {'id':'kpi_2','column':4,'row':1,'span':3},
        {'id':'kpi_3','column':7,'row':1,'span':3},
        {'id':'kpi_4','column':10,'row':1,'span':3},
        {'id':'primary_visual','column':1,'row':2,'span':8,'row_span':2},
        {'id':'secondary_visual','column':9,'row':2,'span':4,'row_span':2},
    ])
