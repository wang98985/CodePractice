from django.db import migrations


def backfill_nickname(apps, schema_editor):
    """登录改为邮箱后 username 不再对外暴露，把历史用户的展示名回填到 nickname。"""
    User = apps.get_model("accounts", "User")
    for user in User.objects.filter(nickname=""):
        user.nickname = user.username or ""
        user.save(update_fields=["nickname"])


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_user_bio_user_nickname"),
    ]

    operations = [
        migrations.RunPython(backfill_nickname, migrations.RunPython.noop),
    ]
