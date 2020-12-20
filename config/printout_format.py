def msg_form(line1,line2="",form1="",form2="",lcd_columns=16, lcd_rows=2):
    if type(line1) is tuple:
        line2 = str(line1[1])
        line1 = str(line1[0])
    if form1=="": form1="{}"
    if form2=="": form2="{}"
    line1 = form1.format(line1)[:lcd_columns]
    line2 = form2.format(line2)[:lcd_columns]
    line_form = "{}\n{}"
    msg_str = line_form.format(line1,line2)
    return msg_str

def lcd_ribbon(lcd_columns=16, lcd_rows=2):
    return msg_form(">"*lcd_columns,"<"*lcd_columns)

def lcd_info():
    return msg_form("<Insert> Info","<End> Exit")