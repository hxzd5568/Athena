# Templates for generate SplitOp/SliceOp.
class split_index_codegen:
  def __init__(self):
    pass

  def get_split_index(axis, sections):
    sec_num = len(sections)
    coord_list[3] = ["coord.batch", "coord.row", "coord.column"]
    axis_code = coord_list[axis]
    new_sections = MutableList()
    new_sections.append(0) 
    def accumulate_sections(i):
      split_start = int(new_sections[i])
      dim_stop = split_start + sections[i]
      new_sections.append(dim_stop)
    # INDEX_START_CODE = """
    #   coord.batch < new_sections[1] ? 0
    #                             : coord.batch < new_sections[2] ? new_sections[1]
    #                             : new_sections[2];
    # """
    index_start_code = ""
    def generate_offset_code(i):
      start_code_branch = f"{axis_code} < {new_sections[i+1]} ? {new_sections[i]}\n :"
      index_start_code = index_start_code + start_code_branch
    map(generate_offset_code, sec_num - 1)
    index_start_code = index_start_code + f"{new_sections[sec_num - 1]}"
    

    split_index_along_axis0_code = """
      int batch_start = ${INDEX_START_CODE} 
      int base_index = batch_start * args.input0_dim1 * args.input1_dim1;
    """

    split_index_along_axis1_code = """
      int row_start = ${INDEX_START_CODE}
      int base_index = coord.batch * row_start * args.input1_dim1 + row_start * (coord.column + 1);
    """

    split_index_along_axis2_code = """
      int column_start = ${INDEX_START_CODE}
      int base_index = coord.batch * args.input0_dim1 * column_start + args.input0_dim1 * column_start;
    """
    split_index = split_index_along_axis0_code if axis == 0
                                               else split_index_along_axis1_code if axis == 1
                                               else split_index_along_axis2_code
    return split_index.replace("${INDEX_START_CODE}", index_start_code)

  def get_split_ptr_id(axis, sec_num, shape):
    coord_list[3] = ["coord.batch", "coord.row", "coord.column"]
    axis_code = coord_list[axis]
    return ptr_id = f"{axis_code} / ({shape[axis]} / {sec_num})"

  def get_split_ptr_id(axis, sections):
    sec_num = len(sections)
    coord_list[3] = ["coord.batch", "coord.row", "coord.column"]    
    axis_code = coord_list[axis]
    new_sections = MutableList()
    new_sections.append(0) 
    def accumulate_sections(i):
      split_start = int(new_sections[i])
      dim_stop = split_start + sections[i]
      new_sections.append(dim_stop)
    map(accumulate_sections, range(sec_num))
    # PTR_ID_CODE = f"""
    #   {axis_code} < sections[1] ? 0
    #                             : {axis_code} < sections[2] ? 1
    #                             : {axis_code} < sections[3] ? 2
    #                             : {axis_code} < sections[4] ? 3
    #                             ...
    #                             : sec_num - 1
    # """
    PTR_ID_CODE = ""
    def generate_ptr_id_code(i):
      ptr_id_code_branch = f"{axis_code} < {new_sections[i+1]} ? {i}\n :"
      PTR_ID_CODE = PTR_ID_CODE + ptr_id_code_branch
    map(generate_ptr_id_code, range(sec_num - 1))
    PTR_ID_CODE = PTR_ID_CODE + f"{sec_num - 1}"
    return PTR_ID_CODE

  def get_slice_index():
    slice_index_code = """
      int linear_index = coord.batch * args.input0_dim1 * args.input1_dim1 +
                  coord.row * args.input1_dim1 + coord.column;
      int batch_base_index = starts[0] * shape[1] * args.input0_dim1;
      int row_base_index = starts[1] * args.input0_dim1;
      int column_base_index = args.input1_dim1;
      int slice_index = linear_index - batch_base_index - row_base_index - column_base_index;
    """
    slice_condition_code = """
      bool condition_batch = coord.batch > starts[0] && coord.batch < ends[0];
      bool condition_row = coord.row > starts[1] && coord.row < ends[1];
      bool condition_column = coord.column > starts[2] && coord.column < ends[2];
      bool condition_batch && condition_column && condition_row;
    """
    return f"if {slice_condition_code}\n    {slice_index_code}"

