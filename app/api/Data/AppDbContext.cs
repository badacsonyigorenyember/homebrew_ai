using Microsoft.EntityFrameworkCore;

namespace HomebrewApp.Data;

public class AppDbContext : DbContext
{
    public DbSet<Recipe> Recipes => Set<Recipe>();
    public DbSet<RecipeItem> RecipeItems => Set<RecipeItem>();
    public DbSet<BeerStyle> BeerStyles => Set<BeerStyle>();
    public DbSet<Ingredient> Ingredients => Set<Ingredient>();
    
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options)
    {
        
    }
}