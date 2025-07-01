# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

class LaptopInfo(models.Model):
    cam_ung = models.IntegerField(blank=True, null=True) # categorical 0 - 1
    height_mm = models.FloatField(blank=True, null=True) # numerical
    url_path = models.CharField(max_length=128, blank=True, null=True)
    material = models.CharField(max_length=50, blank=True, null=True) # categorical
    storage_max_support = models.FloatField(blank=True, null=True) # numerical
    storage_gb = models.FloatField(blank=True, null=True) # numerical
    display_width = models.FloatField(blank=True, null=True) # numerical
    bluetooth_version = models.FloatField(blank=True, null=True)
    width_mm = models.FloatField(blank=True, null=True)
    manufacturer = models.CharField(max_length=50, blank=True, null=True) # categorical
    cpu_max_speed = models.FloatField(blank=True, null=True) # numerical
    root_price = models.FloatField(blank=True, null=True) # numerical
    cpu_threads = models.FloatField(blank=True, null=True) # numerical
    cpu_cores = models.FloatField(blank=True, null=True) # numerical
    ram_speed = models.FloatField(blank=True, null=True) # numerical
    product_weight = models.FloatField(blank=True, null=True) # numerical
    discounted_price = models.FloatField(blank=True, null=True)
    ram_type = models.CharField(max_length=50, blank=True, null=True) # categorical
    refresh_rate = models.FloatField(blank=True, null=True) # numerial
    cpu_speed = models.FloatField(blank=True, null=True) # numerical
    name = models.CharField(max_length=128, blank=True, null=True)
    ram_storage = models.FloatField(blank=True, null=True) # numerical
    is_installment = models.IntegerField(blank=True, null=True) 
    ram_slots = models.FloatField(blank=True, null=True) # numerical
    os_version = models.CharField(max_length=50, blank=True, null=True) # categorical
    battery_capacity = models.FloatField(blank=True, null=True) # numerical
    laptop_color = models.CharField(max_length=50, blank=True, null=True) # categorical
    cpu_model = models.CharField(max_length=50, blank=True, null=True) # categorical
    vga_type = models.CharField(max_length=50, blank=True, null=True) # categorical
    depth_mm = models.FloatField(blank=True, null=True) # numerical
    image = models.CharField(max_length=256, blank=True, null=True)
    vga_brand = models.CharField(max_length=50, blank=True, null=True) # categorical
    product_id = models.CharField(max_length=50, primary_key=True, db_column='product_id') # categorical # Primary key
    cpu_series = models.CharField(max_length=50, blank=True, null=True) # categorical
    display_height = models.FloatField(blank=True, null=True) # numerical
    vga_vram = models.FloatField(blank=True, null=True) # numerical
    laptop_camera = models.CharField(max_length=50, blank=True, null=True) # categorical
    display_size = models.FloatField(blank=True, null=True) # numerical
    cpu_brand = models.CharField(max_length=50, blank=True, null=True) # categorical
    hoc_tap_van_phong = models.IntegerField(blank=True, null=True) # categorical
    laptop_sang_tao_noi_dung = models.IntegerField(blank=True, null=True) # categorical
    mong_nhe = models.IntegerField(blank=True, null=True) # categorical
    gaming = models.IntegerField(blank=True, null=True) # categorical
    do_hoa_ky_thuat = models.IntegerField(blank=True, null=True) # categorical
    cao_cap_sang_trong = models.IntegerField(blank=True, null=True) # categorical

    class Meta:
        managed = False
        db_table = 'laptop_info'