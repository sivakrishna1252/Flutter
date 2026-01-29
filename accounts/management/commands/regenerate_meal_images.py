from django.core.management.base import BaseCommand
from accounts.models import MealRecommendation
from accounts.ai_recommender import get_fallback_image_url


class Command(BaseCommand):
    help = 'Regenerate image URLs for all cached meal recommendations'

    def handle(self, *args, **options):
        # Get all meal recommendations
        recommendations = MealRecommendation.objects.all()
        
        if not recommendations.exists():
            self.stdout.write(self.style.WARNING('No meal recommendations found'))
            return
        
        updated_count = 0
        
        for rec in recommendations:
            items = rec.items_json
            
            # Check if items have empty image_urls
            needs_update = False
            for item in items:
                if not item.get('image_url'):
                    needs_update = True
                    # Generate fallback image URL
                    item_name = item.get('name', 'Food')
                    item['image_url'] = get_fallback_image_url(item_name)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Generated image URL for: {item_name} -> {item["image_url"][:50]}...'
                        )
                    )
            
            # Save updated items back to database
            if needs_update:
                rec.items_json = items
                rec.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Updated: {rec.user.mobile} - {rec.date} - {rec.meal_type}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Successfully updated {updated_count} recommendations with image URLs')
        )
