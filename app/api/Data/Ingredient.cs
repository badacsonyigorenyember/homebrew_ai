using System.ComponentModel.DataAnnotations.Schema;

namespace HomebrewApp.Data;

[Table("ingredient", Schema = "ref")]
public class Ingredient
{
    [Column("id")]
    public long Id { get; init; }

    [Column("kind")]
    public required string Kind { get; init; }

    [Column("name")]
    public required string Name { get; init; }

    [Column("producer")]
    public required string Producer { get; init; }
}
