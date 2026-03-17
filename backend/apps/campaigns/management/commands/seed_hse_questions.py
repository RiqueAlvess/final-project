"""
Management command to seed the HSE-IT questionnaire dimensions and questions.

Usage:
    python manage.py seed_hse_questions
    python manage.py seed_hse_questions --tenant demo  (schema-aware)
"""

from django.core.management.base import BaseCommand

from apps.campaigns.models import HSEDimension, HSEQuestion


HSE_DATA = [
    {
        'name': 'Demandas',
        'type': 'NEGATIVE',
        'order': 1,
        'questions': [
            'Tenho que trabalhar em ritmo muito intenso.',
            'Tenho prazos impossíveis de cumprir.',
            'Tenho que negligenciar algumas tarefas por ter muito trabalho a fazer.',
            'Diferentes grupos de pessoas no trabalho me fazem exigências conflitantes.',
            'Tenho tempo suficiente para realizar meu trabalho.',
        ],
    },
    {
        'name': 'Controle',
        'type': 'POSITIVE',
        'order': 2,
        'questions': [
            'Posso decidir quando fazer uma pausa.',
            'Tenho voz ativa sobre como faço meu trabalho.',
            'Tenho liberdade para decidir o que fazer no trabalho.',
            'Minhas horas de trabalho são flexíveis.',
            'Tenho autonomia para desenvolver minhas habilidades no trabalho.',
        ],
    },
    {
        'name': 'Apoio da Chefia',
        'type': 'POSITIVE',
        'order': 3,
        'questions': [
            'Posso contar com meu gestor para me ajudar com um problema no trabalho.',
            'Recebo feedback útil do meu gestor sobre o meu desempenho.',
            'Meu gestor me apoia suficientemente.',
            'Meu gestor se preocupa com meu bem-estar.',
            'Meu gestor encoraja-me a questionar atitudes inadequadas no trabalho.',
        ],
    },
    {
        'name': 'Apoio dos Colegas',
        'type': 'POSITIVE',
        'order': 4,
        'questions': [
            'Posso contar com meus colegas para me ajudar com um problema no trabalho.',
            'Recebo ajuda e suporte dos meus colegas.',
            'Meus colegas se preocupam com meu bem-estar.',
            'As pessoas com quem trabalho têm uma atitude positiva em relação ao trabalho.',
            'As pessoas com quem trabalho me tratam com respeito.',
        ],
    },
    {
        'name': 'Relacionamentos',
        'type': 'NEGATIVE',
        'order': 5,
        'questions': [
            'Estou sujeito(a) a comportamento pessoalmente ofensivo no trabalho.',
            'Existem conflitos e tensões entre colegas no meu ambiente de trabalho.',
            'Meus colegas se comportam de forma rude comigo no trabalho.',
            'Há situações de intimidação ou assédio no trabalho.',
            'As relações de trabalho são tensas e difíceis.',
        ],
    },
    {
        'name': 'Cargo/Função',
        'type': 'POSITIVE',
        'order': 6,
        'questions': [
            'Sei claramente o que é esperado de mim no trabalho.',
            'Sei quais são minhas responsabilidades.',
            'Compreendo como meu trabalho contribui para os objetivos da organização.',
            'Tenho objetivos e metas claros para meu trabalho.',
            'Compreendo o propósito e a missão da minha organização.',
        ],
    },
    {
        'name': 'Comunicação e Mudanças',
        'type': 'POSITIVE',
        'order': 7,
        'questions': [
            'Tenho a oportunidade de questionar gestores sobre mudanças que afetam meu trabalho.',
            'Os colaboradores são consultados sobre mudanças no trabalho.',
            'Quando há mudanças, sou informado(a) claramente de como isso afetará meu trabalho.',
            'A liderança faz bom uso das habilidades das pessoas.',
            'A liderança fornece informações adequadas sobre mudanças propostas.',
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed HSE-IT dimensions and questions into the database.'

    def handle(self, *args, **options) -> None:
        created_dims = 0
        created_qs = 0

        for dim_data in HSE_DATA:
            dim, dim_created = HSEDimension.objects.get_or_create(
                name=dim_data['name'],
                defaults={
                    'dimension_type': dim_data['type'],
                    'order': dim_data['order'],
                },
            )
            if dim_created:
                created_dims += 1

            for q_order, q_text in enumerate(dim_data['questions'], start=1):
                _, q_created = HSEQuestion.objects.get_or_create(
                    dimension=dim,
                    order=q_order,
                    defaults={'text': q_text},
                )
                if q_created:
                    created_qs += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Done. Created {created_dims} dimension(s) and {created_qs} question(s).'
            )
        )
