from users.models import User
from users.models import Tier

enterprise_plan = Tier.objects.get(name='Enterprise')

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(username='admin', password='admin', tier=enterprise_plan)
