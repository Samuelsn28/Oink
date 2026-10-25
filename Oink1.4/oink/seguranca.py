"""Bloqueio de dados sensíveis (CPF) ANTES de a mensagem chegar à IA."""
import re


def cpf_valido(texto: str) -> bool:
    """Confere os dois dígitos verificadores do CPF."""
    nums = [int(d) for d in texto if d.isdigit()]
    if len(nums) != 11 or len(set(nums)) == 1:  # 111.111.111-11 etc. são inválidos
        return False
    for i in (9, 10):
        soma = sum(n * p for n, p in zip(nums[:i], range(i + 1, 1, -1)))
        if nums[i] != (soma * 10 % 11) % 10:
            return False
    return True


# 11 dígitos, com ou sem pontos, traços, barras ou espaços no meio
PADRAO_11_DIGITOS = re.compile(r"(?<!\d)(?:\d[\s.\-/]*){11}(?!\d)")
# formato clássico 000.000.000-00
PADRAO_FORMATADO = re.compile(r"(?<!\d)\d{3}\.\d{3}\.\d{3}-\d{2}(?!\d)")


def contem_cpf(texto: str) -> bool:
    # 1) formato clássico: bloqueia sempre, mesmo com dígitos inventados
    if PADRAO_FORMATADO.search(texto):
        return True
    # 2) outras sequências de 11 dígitos: só bloqueia se for um CPF válido
    #    (assim telefones e valores não são bloqueados por engano)
    return any(cpf_valido(m.group()) for m in PADRAO_11_DIGITOS.finditer(texto))
