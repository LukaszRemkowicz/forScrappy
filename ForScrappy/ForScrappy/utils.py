import re


def eval_simple_function(string):
    first_num = 0
    second_num = 0
    listed = re.findall(r'\+|\*|\-|\%|[0-9]+', string[1:-1])

    multi = False
    div = False
    minus = False
    rest = False
    res_result = False

    """function not finished. Need to add recurrence with () operations"""
    # if '(' in string:
    #     req_list = re.sub(r'(.+)(\()(.+)(\))', r'\3', ' '.join(string))
    #     res_result = funcja(req_list)

    for element in listed:
        if element == '*':
            multi = True
        elif element == '/':
            div = True
        elif element == '-':
            minus = True
        elif element == '%':
            rest = True
        elif element == '+':
            first_num += second_num
            second_num = 0
            multi = False
            div = False
            minus = False
            rest = False
        else:
            if multi:
                second_num *= int(element)
                multi = False
            elif div:
                second_num /= int(element)
                div = False
            elif minus:
                second_num -= int(element)
                mins = False
            elif rest:
                second_num %= int(element)
                rest = False
            else:
                second_num += int(element)

    return first_num + second_num
