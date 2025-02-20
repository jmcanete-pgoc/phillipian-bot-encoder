from django.db import models

class AreaInfo(models.Model):
    barangay = models.TextField(blank=True, null=True)  # Allows blank and null values
    city = models.TextField(blank=True, null=True)
    province = models.TextField(blank=True, null=True)
    commune_id = models.TextField(blank=True, null=True)
    district_id = models.TextField(blank=True, null=True)
    province_id = models.TextField(blank=True, null=True)
    ai_province = models.TextField(blank=True, null=True)
    ai_city = models.TextField(blank=True, null=True)
    ai_barangay = models.TextField(blank=True, null=True)

    class Meta:
        # You can add indexes for frequently queried fields to improve performance.
        indexes = [
            models.Index(fields=['barangay'], name='barangay_idx'),
            models.Index(fields=['city'], name='city_idx'),
            models.Index(fields=['province'], name='province_idx'),
            models.Index(fields=['commune_id'], name='commune_id_idx'),
            models.Index(fields=['district_id'], name='district_id_idx'),
            models.Index(fields=['province_id'], name='province_id_idx'),
            # Add more indexes as needed based on your queries.
        ]

        # Use a composite unique constraint if you want to prevent duplicate combinations
        # of certain fields.  For example, if you want to ensure unique combinations of 
        # barangay, city, and province:
        # unique_together = ('barangay', 'city', 'province')

    def __str__(self):
        # Human-readable representation of the object.
        return f"{self.barangay}, {self.city}, {self.province}" 
        # Customize this based on the fields that best identify the record.




class PhilippineAddress(models.Model):
    island = models.TextField(blank=True, null=True)
    region = models.TextField(blank=True, null=True)
    province = models.TextField(blank=True, null=True)
    municipality_city = models.TextField(blank=True, null=True)  # Renamed for PEP 8 compliance
    barangay = models.TextField(blank=True, null=True)
    postal = models.TextField(blank=True, null=True)
    latitude = models.TextField(blank=True, null=True)
    longitude = models.TextField(blank=True, null=True)

    class Meta:
        # Add indexes for frequently queried fields
        indexes = [
            models.Index(fields=['region'], name='ph_region_idx'),
            models.Index(fields=['province'], name='ph_province_idx'),
            models.Index(fields=['municipality_city'], name='ph_municipality_city_idx'),
            models.Index(fields=['barangay'], name='ph_barangay_idx'),
            # ... add more indexes as needed
        ]
        # unique_together = ('island', 'region', 'province', 'municipality_city', 'barangay')  # If needed

    def __str__(self):
        return f"{self.barangay}, {self.municipality_city}, {self.province}"  # Customize as needed