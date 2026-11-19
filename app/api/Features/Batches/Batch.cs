using System.ComponentModel.DataAnnotations.Schema;

namespace HomebrewApp.Features.Batches;

[Table("batch", Schema = "app")]
public class Batch
{
    [Column("id")]
    public long Id { get; init; }

    [Column("number")]
    public required int Number { get; init; }

    [Column("name")]
    public required string Name { get; init; }

    [Column("recipe_id")]
    public long RecipeId { get; init; }

    [Column("brew_date")]
    public required DateOnly BrewDate { get; init; }

    [Column("status")]
    public required string Status { get; init; }

    [Column("batch_l")]
    public required decimal BatchL { get; init; }

    [Column("efficiency_pct")]
    public required decimal EfficiencyPct { get; init; }

    [Column("process", TypeName = "jsonb")]
    public required string Process { get; init; }

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

    [Column("locked_at")]
    public DateTime? LockedAt { get; init; }

    [Column("created_at")]
    [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
    public DateTime CreatedAt { get; init; }
}
