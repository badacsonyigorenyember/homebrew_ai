using System.ComponentModel.DataAnnotations.Schema;

namespace HomebrewApp.Data;

[Table("recipe", Schema = "app")]
public class Recipe
{
    [Column("id")]
    public long Id { get; init; }

    [Column("style_id")]
    public required long StyleId { get; init; }

    public BeerStyle Style { get; init; } = null!;

    [Column("status")]
    public required string Status { get; init; }

    [Column("batch_l")]
    public required decimal BatchL { get; init; }

    [Column("efficiency_pct")]
    public required decimal EfficiencyPct { get; init; }

    [Column("og")]
    public decimal? OG { get; init; }

    [Column("fg")]
    public decimal? FG { get; init; }

    [Column("abv")]
    public decimal? ABV { get; init; }

    [Column("ibu")]
    public decimal? IBU { get; init; }

    [Column("srm")]
    public decimal? SRM { get; init; }

    [Column("process", TypeName = "jsonb")]
    public string? Process { get; init; }

    [Column("created_at")]
    public required DateTime CreatedAt { get; init; }

    public List<RecipeItem> Items { get; init; } = [];
}
