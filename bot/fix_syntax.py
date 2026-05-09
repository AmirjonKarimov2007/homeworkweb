import sys
with open('handlers.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix syntax errors - remove extra }
old1 = "parts.append(f\"\U0001f4c5 deadline: {detail.homework_due_date.strftime('%d.%m.%Y %H:%M')}\")"
new1 = "parts.append(f\"\U0001f4c5 deadline: {detail.homework_due_date.strftime('%d.%m.%Y %H:%M')}\")"

content = content.replace(old1, new1)

old2 = "text.append(f\"\U0001f4c5 deadline: {result['due_date'].strftime('%d.%m.%Y %H:%M')}\")"
new2 = "text.append(f\"\U0001f4c5 deadline: {result['due_date'].strftime('%d.%m.%Y %H:%M')}\")"

content = content.replace(old2, new2)

with open('handlers.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed!')
