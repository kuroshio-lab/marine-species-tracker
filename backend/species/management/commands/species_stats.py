# species/management/commands/species_stats.py
from django.core.management.base import BaseCommand
from species.models import CuratedObservation
from django.db.models import Count, Min, Max, Q


class Command(BaseCommand):
    help = "Display Kuroshio-Lab species observation statistics"

    def handle(self, *args, **options):
        total = CuratedObservation.objects.count()

        obis_only = CuratedObservation.objects.filter(source="OBIS").count()
        gbif_only = CuratedObservation.objects.filter(source="GBIF").count()
        both = CuratedObservation.objects.filter(source="BOTH").count()

        date_range = CuratedObservation.objects.aggregate(
            oldest=Min("observation_date"), newest=Max("observation_date")
        )

        with_depth = CuratedObservation.objects.filter(
            Q(depth_min__isnull=False)
            | Q(depth_max__isnull=False)
            | Q(bathymetry__isnull=False)
        ).count()

        with_common_name = (
            CuratedObservation.objects.filter(common_name__isnull=False)
            .exclude(common_name="")
            .count()
        )

        top_species = (
            CuratedObservation.objects.values("species_name", "common_name")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        duplicate_check = (
            CuratedObservation.objects.values("occurrence_id")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
            .count()
        )

        self.stdout.write(
            f"""
╔════════════════════════════════════════════════════╗
║   🌊 Kuroshio-Lab Observation Statistics          ║
╚════════════════════════════════════════════════════╝

📊 Total Observations: {total:,}

🗂️  Source Breakdown:
   • OBIS only:        {obis_only:,}  ({obis_only/total*100:.1f}% if total else 0)
   • GBIF only:        {gbif_only:,}  ({gbif_only/total*100:.1f}% if total else 0)
   • Both (merged):    {both:,}  ({both/total*100:.1f}% if total else 0)

📅 Temporal Coverage:
   • Oldest:  {date_range['oldest']}
   • Newest:  {date_range['newest']}

✅ Data Quality:
   • With depth data:   {with_depth:,}  ({with_depth/total*100:.1f}% if total else 0)
   • With common name:  {with_common_name:,}  ({with_common_name/total*100:.1f}% if total else 0)

⚠️  Deduplication Health:
   • Duplicate occurrence_ids: {duplicate_check}
   {"✅ All clean!" if duplicate_check == 0 else "⚠️  Run: python manage.py deduplicate_observations"}

🐟 Top 10 Most Observed Species:
        """
        )

        for i, species in enumerate(top_species, 1):
            common = species["common_name"] or "No common name"
            self.stdout.write(
                f"   {i:2}. {species['species_name']:<40}\n"
                f"       ({common}) - {species['count']:,} observations"
            )

        self.stdout.write("\n" + "=" * 52)
