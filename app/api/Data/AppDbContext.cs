using Microsoft.EntityFrameworkCore;

namespace HomebrewApp.Data;

public class AppDbContext(DbContextOptions<AppDbContext> options) : DbContext(options)
{
    public DbSet<Recipe> Recipes => Set<Recipe>();
    public DbSet<RecipeItem> RecipeItems => Set<RecipeItem>();
    public DbSet<BeerStyle> BeerStyles => Set<BeerStyle>();
    public DbSet<Ingredient> Ingredients => Set<Ingredient>();
}