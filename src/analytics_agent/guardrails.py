import sqlglot
from sqlglot import exp

ALLOWED_COLUMNS = {"event_id", "channel", "converted"}

def validate_sql(sql):
    if not isinstance(sql, str) or not sql.strip() or len(sql) > 8000:
        raise ValueError("SQL must be nonempty and at most 8,000 characters.")
    try:
        statements = sqlglot.parse(sql, read="sqlite")
    except sqlglot.errors.ParseError as exc:
        raise ValueError("SQL could not be parsed.") from exc
    if len(statements) != 1 or not isinstance(statements[0], exp.Select):
        raise ValueError("Exactly one SELECT statement is allowed.")
    tree = statements[0]
    if len(list(tree.find_all(exp.Select))) != 1:
        raise ValueError("Nested queries are outside this prototype's scope.")
    for key in ["with_", "with", "joins", "group", "having", "limit", "offset", "distinct", "into", "qualify", "windows", "locks"]:
        if tree.args.get(key):
            raise ValueError("Use an unaggregated single-table event query without sampling or limits.")
    tables = list(tree.find_all(exp.Table))
    if len(tables) != 1 or tables[0].name.lower() != "marketing_events" or tables[0].db or tables[0].catalog:
        raise ValueError("Only the marketing_events table is allowed.")
    expected = ["event_id", "channel", "converted"]
    if len(tree.expressions) != 3 or any(not isinstance(c, exp.Column) or c.name.lower() != name for c, name in zip(tree.expressions, expected)):
        raise ValueError("Select the unchanged event_id, channel, converted columns, in that order.")
    if any(c.name.lower() not in ALLOWED_COLUMNS for c in tree.find_all(exp.Column)):
        raise ValueError("Unknown column.")
    if any(isinstance(node, (exp.Func, exp.Subquery, exp.Star)) for node in tree.walk()):
        raise ValueError("Functions, subqueries and stars are not supported.")
    warnings = []
    if tree.args.get("where"):
        warnings.append("Filtered sample: results describe only selected events; selection may affect comparisons.")
    return tree.sql(dialect="sqlite"), warnings
