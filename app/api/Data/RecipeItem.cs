using System.ComponentModel.DataAnnotations.Schema;

namespace HomebrewApp.Data;

[Table("recipe_item", Schema = "app")]
public class RecipeItem
{
    [Column("id")]
    public long Id { get; init; }

    [Column("recipe_id")]
    public required long RecipeId { get; init; }

    [Column("ingredient_id")]
    public long? IngredientId { get; init; }

    public Ingredient? Ingredient { get; init; }

    [Column("raw_name")]
    public required string RawName { get; init; }

    [Column("usage")]
    public required string Usage { get; init; }

    [Column("time_min")]
    public decimal? TimeMin { get; init; }

    [Column("pct")]
    public decimal? Percentage { get; init; }

    [Column("amount")]
    public required decimal Amount { get; init; }

    [Column("unit")]
    public required string Unit { get; init; }
}
