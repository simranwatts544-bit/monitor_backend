# yourapp/management/commands/seed_vms_and_sources.py

from django.core.management.base import BaseCommand
from django.db import transaction
from source_manager.models import VM, Source

class Command(BaseCommand):
    help = 'Seeds initial VMs and their sources (idempotent)'

    def handle(self, *args, **options):

        data = {
            "161.168.121.25": ["Facebook 1", "Facebook 2", "Facebook 3", "facebook real time"],
            "161.168.121.96": ["facebook", "facebook1", "facebook2"],
            "161.168.121.97": ["facebook_profile1", "facebook_profile", "facebook_profile2", "facebook profile search"],
            "161.168.121.192": ["facebook keyword ", "douban"],
            "161.168.121.202": ["vk", "reddit", "flickr", "darkweb", "discord (xcdp)", "twitter link analysis", "reddit consumer"],
            "161.168.121.205": [
                "reddit", "flickr", "darkweb", "telegram", "pinterest profile", "chirpwire keyword",
                "federated search", "telegram consumer", "weibo profile", "(baidu/sogou/360) fed_search",
                "vk", "pinterest profile consumer", "chirpwire keyword consumer", "facebook",
                "searchProfileApi_telegram", "searchProfileApi"
            ],
            "161.168.121.206": ["moimir", "pinterest keyword", "ok"],
            "161.168.121.207": [
                "twitter profile", "wordpress", "yt docker", "instaApi keyword",
                "instagram link analysis", "instagam api profile", "twitter fetch result", "wordpress consumer"
            ],
            "161.168.121.212": ["twitter profile", "yt", "facebook consumer", "yt consumer docker", "twitter profile scraper result"],
            "161.168.121.213": ["twitter keyword"],
            "161.168.121.217": ["chirpwire keyword", "pinterest profile", "youtube", "linkedin", "telegram", "youtube  consumer"],
            "161.168.121.218": ["rutube", "rutube consumer", "rutube consumer docker", "tumblr", "tumblr consumer", "tiktok", "tiktok consumer"],
            "161.168.121.220": ["weibo", "weibo consumer"],
            "161.168.121.222": ["google news", "dailymotion keyword", "qq consumer", "dailymotion", "consumer dailymotion"],
            "161.168.121.225": ["Tiktok", "tumblr consumer", "ask"],
            "164.52.219.142": ["douyin", "Youku", "qq", "weibo profile"],
            "161.168.121.226": ["twitter profile search", "google blogs"],
            "161.168.121.227": ["xiahongshu consumer", "douban consumer", "douyin consumer", "google blogs"],
            "161.168.121.229": ["Toutiao"],
            "164.52.219.154": ["qq", "tencent video", "douyin", "Youku"],
            "164.52.219.133": ["qq", "douban", "toutiao", "xiaohongshu"],
            "164.52.219.59":  ["toutiao", "qq"],
            "164.52.219.27":  ["douban", "weibo profile", "qq", "Tencent Video", "xiaohongshu"],
            "161.168.121.26":  ["twitter real time keyword", "twitter profile results"],
            "161.168.121.33":  ["xiahongshu"],
            "161.168.121.32":  ["Youku"],
            "161.168.121.24":  ["tiktok"],
            "161.168.121.224": ["website"],
        }

        created_vms = 0
        created_sources = 0

        with transaction.atomic():
            for ip, sources_list in data.items():
                vm, vm_created = VM.objects.get_or_create(
                    ip_address=ip.strip(),
                    defaults={'name': f"VM-{ip.split('.')[-1]}"}
                )
                if vm_created:
                    created_vms += 1

                for source_name in sources_list:
                    cleaned_name = source_name.strip()
                    cleaned_lower = cleaned_name.lower()

                    # Your requested rule:
                    # Contains "profile" (case-insensitive) → profile-based
                    # Otherwise → keyword-based
                    if 'profile' in cleaned_lower:
                        is_keyword_based = False
                        is_profile_based = True
                    else:
                        is_keyword_based = True
                        is_profile_based = False

                    _, source_created = Source.objects.get_or_create(
                        vm=vm,
                        name=cleaned_name,
                        defaults={
                            'profile': cleaned_name.lower().replace(' ', '_')[:90],
                            'is_keyword_based': is_keyword_based,
                            'is_profile_based': is_profile_based,
                        }
                    )
                    if source_created:
                        created_sources += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done.\n"
            f"VMs created: {created_vms}\n"
            f"Sources created: {created_sources}\n"
            f"(already existing records were skipped)"
        ))