using System.ComponentModel.DataAnnotations.Schema;

namespace HomebrewApp.Features.Batches;

[Table("batch_item", Schema = "app")]
public class BatchItem
{
    [Column("id")]
    public long Id { get; init; }

    [Column("batch_id")]
    public long BatchId { get; init; }

    [Column("source_item_id")]
    public long? SourceItemId { get; init; }

    [Column("ingredient_id")]
    public long? IngredientId { get; init; }

    [Column("raw_name")]
    public required string RawName { get; init; }

    [Column("usage")]
    public required string Usage { get; init; }

    [Column("time_min")]
    public decimal? TimeMin { get; init; }

    [Column("pct")]
    public decimal? Pct { get; init; }

    [Column("amount")]
    public required decimal Amount { get; init; }

    [Column("unit")]
    public required string Unit { get; init; }

    [Column("changed")]
    public required bool Changed { get; init; }
}
