from deepdiff import DeepDiff
import difflib, json, sys

def compare(old: dict, new: dict) -> dict:
    diffs: dict = DeepDiff(old, new, ignore_type_in_groups=[dict]).to_dict()
    if diffs == {}: return diffs
    simplify(diffs)
    return diffs

def simplify(diffs: dict):
    """flatten certain values to lists"""
    fields = ['dictionary_item_added', 'dictionary_item_removed', 'type_changes', "iterable_item_removed"]
    for field in fields:
        if field in diffs: diffs[field] = removeRootFromList(list(diffs[field]))
    if "values_changed" in diffs:
        changes: dict = diffs["values_changed"]
        # replace "values changed" dict with separate changes, each on one line
        for key in changes:
            change: dict = changes[key]
            oldVal = change["old_value"]
            newVal = change["new_value"]
            inlineDiff = genericCall(oldVal, newVal)
            if inlineDiff != None:
                # remove "root" from keys
                diffs[removeRoot(key)] = inlineDiff
        # pop now redundant "values changed" key/ value pair
        diffs.pop("values_changed")

def removeRootFromList(s: list[str]) -> list:
    clean = [removeRoot(line) for line in s]
    return clean

def removeRoot(s: str) -> str:
    return s.split("root")[-1]

def genericCall(a, b) -> str | None:
    """entry point for comparison functions"""
    # invalid
    if type(a) != type(b): return None
    # no changes
    if a == b: return None
    match a:
        case str(): return diffStrings(a, b)
        case int() | float(): return diffNumbers(a, b)
        case _: return None


def diffNumbers(x: int|float|str, y: int|float|str):
    """for numbers or single words"""
    return f"{x} -> {y}"

def diffStrings(a: str, b: str) -> str:
    """for sentences"""
    if one_or_no_words(a) and one_or_no_words(b): 
        # if only one or no words, use simpler version
        return diffNumbers(a, b)
    matcher = difflib.SequenceMatcher(None, a, b)
    result = [] # writing to list and converting it to string after is more efficient
    
    for tag, aStart, aEnd, bStart, bEnd in matcher.get_opcodes():
        aPart = a[aStart:aEnd]
        bPart = b[bStart:bEnd]
        
        if tag == 'equal':
            result.append(aPart)
        elif tag == 'delete':
            result.append(format_change(aPart, 'delete'))
        elif tag == 'insert':
            result.append(format_change(bPart, 'insert'))
        elif tag == 'replace':
            result.append(format_change(aPart, 'replace_old'))
            result.append(" -> ")
            result.append(format_change(bPart, 'replace_new'))
    
    # cleanup
    diff = ''.join(result)
    return (diff
        .replace('{  ', '{ ')   # Fix double spaces after opening {
        .replace('  }', ' }')   # Fix double spaces before }
        .replace('{}', '')      # Remove empty braces
        .replace('}{', '')      # Fix adjacent braces
    )

def one_or_no_words(s: str) -> bool:
    """check if string is less than two words long"""
    return len(s.split()) < 2

def format_change(part: str, change_type: str) -> str:
    """handles whitespace on both sides of changed text, then places change markers"""
    stripped = part.strip()
    if not stripped:  # Pure whitespace
        return part
    
    # Preserve original spacing
    leading = ' ' if part.startswith(' ') else ''
    trailing = ' ' if part.endswith(' ') else ''
    
    if change_type == 'delete':
        return f"{leading}--{{{stripped}}}{trailing}"
    elif change_type == 'insert':
        return f"{leading}++{{{stripped}}}{trailing}"
    elif change_type == 'replace_old':
        return f"{leading}{{{stripped}"
    elif change_type == 'replace_new':
        return f"{stripped}}}{trailing}"
    
    return part

def main():
    # read json from stdin
    input = sys.stdin.read()
    data = json.loads(input)
    # extract persons
    a: dict = data["a"]
    b: dict = data["b"]
    # compare
    result = compare(a, b)
    # output as json
    print(json.dumps(result))

if __name__ == "__main__":
    main()